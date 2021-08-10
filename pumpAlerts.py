import colorlog, logging
import sys, os
import requests
import time
import yaml

from time import sleep
from sender import TelegramSender


def duration_to_seconds(duration):
    unit = duration[-1]
    if unit == "s":
        unit = 1
    elif unit == "m":
        unit = 60
    elif unit == "h":
        unit = 3600

    return int(duration[:-1]) * unit


def extract_ticker_data(symbol, assets):
    for asset in assets:
        if asset["symbol"] == symbol:
            return asset


def retrieve_exchange_assets(api_url, retry_interval_in_seconds):
    while True:
        try:
            logger.debug(
                "Retrieving price information from the ticker. ApiUrl: %s.", api_url
            )
            return requests.get(api_url).json()
        except Exception as e:
            logger.error(
                "Issue occurred while getting prices. Retrying in %ss. Error: %s.",
                retry_interval_in_seconds,
                e,
                exc_info=True,
            )
            sleep(retry_interval_in_seconds)


def is_symbol_valid(symbol, watchlist, pairs_of_interest):
    # Filter symbols not in watchlist if set
    if len(watchlist) > 0:
        if symbol not in watchlist:
            logger.debug("Ignoring symbol not in watchlist: %s.", symbol)
            return False

    # Removing leverage symbols
    if (
        ("UP" in symbol)
        or ("DOWN" in symbol)
        or ("BULL" in symbol)
        or ("BEAR" in symbol)
    ) and ("SUPER" not in symbol):
        logger.debug("Ignoring leverage symbol: %s.", symbol)
        return False

    # Filter pairsOfInterest to reduce the noise. E.g. BUSD, USDT, ETH, BTC
    if symbol[-4:] not in pairs_of_interest and symbol[-3:] not in pairs_of_interest:
        logger.debug("Ignoring symbol not in pairsOfInterests: %s.", symbol)
        return False

    return True


def filter_and_convert_assets(
    exchange_assets, watchlist, pairs_of_interest, chart_intervals
):
    filtered_assets = []

    for exchange_asset in exchange_assets:
        symbol = exchange_asset["symbol"]

        if is_symbol_valid(symbol, watchlist, pairs_of_interest):
            filtered_assets.append(create_new_asset(symbol, chart_intervals))
            logger.info("Adding symbol: %s.", symbol)

    return filtered_assets


def create_new_asset(symbol, chart_intervals):
    asset = {"symbol": symbol, "price": []}

    for interval in chart_intervals:
        asset[interval] = 0

    return asset


def update_all_monitored_assets_and_send_messages(
    monitored_assets,
    exchange_assets,
    dump_enabled,
    chart_intervals,
    extract_interval_in_seconds,
    outlier_intervals,
):
    for asset in monitored_assets:
        exchange_asset = extract_ticker_data(asset["symbol"], exchange_assets)
        asset["price"].append(float(exchange_asset["price"]))
        asset = calculate_asset_change_and_send_message(
            asset,
            dump_enabled,
            chart_intervals,
            extract_interval_in_seconds,
            outlier_intervals,
        )

    return monitored_assets


def calculate_asset_change_and_send_message(
    asset,
    dump_enabled,
    chart_intervals,
    extract_interval_in_seconds,
    outlier_intervals,
):
    asset_length = len(asset["price"])

    for interval in chart_intervals:

        logger.debug("Calculate asset: %s with interval: %s", asset["symbol"], interval)

        data_points = int(
            chart_intervals[interval]["intervalInSeconds"] / extract_interval_in_seconds
        )

        # If data is not avalilable yet after restart for interval, stop here.
        if data_points >= asset_length:
            logger.debug(
                "Not enough datapoints (%s/%s) for interval: %s",
                asset_length,
                data_points,
                interval,
            )
            break

        # Gets change in % from last alert trigger.
        price_delta = asset["price"][-1] - asset["price"][-1 - data_points]
        change = price_delta / asset["price"][-1]

        # Stores change for the interval into asset dict. Only used for top pump dump report.
        asset[interval] = change

        if abs(change) >= outlier_intervals[interval]:

            if change > 0:
                telegram.send_pump_message(
                    interval,
                    asset["symbol"],
                    change,
                    asset["price"][-1],
                )

            if change < 0 and dump_enabled:
                telegram.send_dump_message(
                    interval,
                    asset["symbol"],
                    change,
                    asset["price"][-1],
                )

    return asset


def reset_prices_data_when_due(
    initial_time_in_seconds, current_time_in_seconds, reset_interval_in_seconds, assets
):
    if current_time_in_seconds - initial_time_in_seconds > reset_interval_in_seconds:

        logger.debug("Emptying price data to prevent memory errors.")
        telegram.send_generic_message("Emptying price data to prevent memory errors.")

        for asset in assets:
            asset["price"] = []

        initial_time_in_seconds = current_time_in_seconds

    return initial_time_in_seconds


def check_to_add_new_asset_listings(
    initial_assets,
    filtered_assets,
    exchange_assets,
    watchlist,
    pairs_of_interest,
    chart_intervals,
):

    if len(initial_assets) >= len(exchange_assets):
        # If initial_assets has more than assets we just ignore it
        logger.debug("No new listing found.")
        return filtered_assets

    init_symbols = [asset["symbol"] for asset in initial_assets]
    retrieved_symbols_to_add = [
        exchange_asset["symbol"]
        for exchange_asset in exchange_assets
        if exchange_asset["symbol"] not in init_symbols
    ]

    logger.debug("New listings found: %s", retrieved_symbols_to_add)

    filtered_symbols_to_add = []
    for symbol in retrieved_symbols_to_add:
        if is_symbol_valid(symbol, watchlist, pairs_of_interest):
            filtered_symbols_to_add.append(symbol)
            filtered_assets.append(create_new_asset(symbol, chart_intervals))

    logger.debug("Filtered new listings found: %s", filtered_symbols_to_add)

    # Sends combined message
    telegram.send_new_listing_message(filtered_symbols_to_add)

    return filtered_assets


def check_to_send_top_pump_dump_statistics_report(
    assets,
    current_time_in_seconds,
    top_report_intervals,
    top_pump_enabled,
    top_dump_enabled,
    additional_stats_enabled,
    no_of_reported_coins,
):

    for interval in top_report_intervals:
        if (
            current_time_in_seconds
            > top_report_intervals[interval]["startTime"]
            + top_report_intervals[interval]["intervalInSeconds"]
            + 8  # Magic number ;)
        ):
            # Update time for new trigger
            top_report_intervals[interval]["startTime"] = current_time_in_seconds

            logger.debug("Sending out top pump dump report. Interval: %s", interval)

            telegram.send_top_pump_dump_statistics_report(
                assets,
                interval,
                top_pump_enabled,
                top_dump_enabled,
                additional_stats_enabled,
                no_of_reported_coins,
            )

        return top_report_intervals


# Read config
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
yaml_file = open(os.path.join(__location__, "config.yml"), "r", encoding="utf-8")
config = yaml.load(yaml_file, Loader=yaml.FullLoader)

# Define the log format
bold_seq = "\033[1m"
log_format = "[%(asctime)s] %(levelname)-8s %(name)-25s %(message)s"
color_format = f"{bold_seq} " "%(log_color)s " f"{log_format}"

colorlog.basicConfig(
    # Define logging level according to the configuration
    level=logging.DEBUG if config["debug"] == True else logging.INFO,
    # Declare the object we created to format the log messages
    format=color_format,
    # Declare handlers for the Console
    handlers=[logging.StreamHandler()],
)

# Define your own logger name
logger = logging.getLogger("binance-pump-alerts")

# Logg whole configuration during the startup
logger.debug("Config: %s", config)

initial_time_in_seconds = time.time()

telegram = TelegramSender(
    token=config["telegramToken"],
    retry_interval=duration_to_seconds(config["telegramRetryInterval"]),
    chat_id=config["telegramChatId"],
    alert_chat_id=config["telegramAlertChatId"]
    if "telegramAlertChatId" in config and config["telegramAlertChatId"] != 0
    else config["telegramChatId"],
    bot_emoji=config["botEmoji"],
    pump_emoji=config["pumpEmoji"],
    dump_emoji=config["dumpEmoji"],
    top_emoji=config["topEmoji"],
    new_listing_emoji=config["newListingEmoji"],
)

extract_interval_in_seconds = duration_to_seconds(config["extractInterval"])
retry_interval_in_seconds = duration_to_seconds(config["priceRetryInterval"])
reset_interval_in_seconds = duration_to_seconds(config["resetInterval"])

chart_intervals = {}
for interval in config["chartIntervals"]:
    chart_intervals[interval] = {}
    chart_intervals[interval]["intervalInSeconds"] = duration_to_seconds(interval)

top_report_intervals = {}
for interval in config["topReportIntervals"]:
    top_report_intervals[interval] = {}
    top_report_intervals[interval]["startTime"] = initial_time_in_seconds
    top_report_intervals[interval]["intervalInSeconds"] = duration_to_seconds(interval)

initial_assets = retrieve_exchange_assets(config["apiUrl"], retry_interval_in_seconds)

filtered_assets = filter_and_convert_assets(
    initial_assets,
    [] if "watchlist" not in config else config["watchlist"],
    config["pairsOfInterest"],
    chart_intervals,
)

telegram.send_generic_message(
    "*Bot has started.* Following _{0}_ pairs.", len(filtered_assets)
)
if "telegramAlertChatId" in config and config["telegramAlertChatId"] != 0:
    telegram.send_generic_message(
        "*Bot has started.* Following _{0}_ pairs.",
        len(filtered_assets),
        is_alert_chat=True,
    )

while True:
    start_loop_time_in_seconds = time.time()

    initial_time_in_seconds = reset_prices_data_when_due(
        initial_time_in_seconds,
        start_loop_time_in_seconds,
        reset_interval_in_seconds,
        filtered_assets,
    )

    exchange_assets = retrieve_exchange_assets(
        config["apiUrl"], retry_interval_in_seconds
    )

    if config["checkNewListingEnabled"]:
        filtered_assets = check_to_add_new_asset_listings(
            initial_assets,
            filtered_assets,
            exchange_assets,
            [] if "watchlist" not in config else config["watchlist"],
            config["pairsOfInterest"],
            chart_intervals,
        )
        # Reset initial exchange asset
        initial_assets = exchange_assets

    filtered_assets = update_all_monitored_assets_and_send_messages(
        filtered_assets,
        exchange_assets,
        config["dumpEnabled"],
        chart_intervals,
        extract_interval_in_seconds,
        config["outlierIntervals"],
    )

    top_report_intervals = check_to_send_top_pump_dump_statistics_report(
        filtered_assets,
        start_loop_time_in_seconds,
        top_report_intervals,
        config["topPumpEnabled"],
        config["topDumpEnabled"],
        config["additionalStatsEnabled"],
        config["noOfReportedCoins"],
    )

    # Sleeps for the remainder of 1s
    sleep(start_loop_time_in_seconds + extract_interval_in_seconds - time.time())
