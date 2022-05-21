import colorlog, logging
import os
import yaml

from alerter import BinancePumpAndDumpAlerter
from reporter import ReportGenerator
from sender import TelegramSender
from utils import ConversionUtils

# Read config
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
config_file = "config.yml"

# Using dev config while development
config_dev_file = "config.dev.yml"
if os.path.isfile(config_dev_file):
    config_file = config_dev_file

yaml_file = open(os.path.join(__location__, config_file), "r", encoding="utf-8")

config = yaml.load(yaml_file, Loader=yaml.FullLoader)

# Define the log format
bold_seq = "\033[1m"
log_format = "[%(asctime)s] %(processName)-12s %(threadName)-23s %(levelname)-8s %(name)-23s %(message)s"
color_format = f"{bold_seq} " "%(log_color)s " f"{log_format}"

colorlog.basicConfig(
    # Define logging level according to the configuration
    level=logging.DEBUG if config["debug"] is True else logging.INFO,
    # Declare the object we created to format the log messages
    format=color_format,
    # Declare handlers for the Console
    handlers=[logging.StreamHandler()],
)

# Define your logger name
logger = logging.getLogger("binance-pump-alerts-app")

# Logg whole configuration during the startup
logger.info("Using config file: %s", config_file)
logger.debug("Config: %s", config)


def main():
    telegram = TelegramSender(
        token=config["telegramToken"],
        chat_id=config["telegramChatId"],
        alert_chat_id=config["telegramAlertChatId"]
        if "telegramAlertChatId" in config and config["telegramAlertChatId"] != 0
        else config["telegramChatId"],
        bot_emoji=config["botEmoji"],
        top_emoji=config["topEmoji"],
        news_emoji=config["newsEmoji"],
    )

    reporter = ReportGenerator(
        telegram=telegram,
        alert_skip_threshold=config["alertSkipThreshold"],
        pump_emoji=config["pumpEmoji"],
        dump_emoji=config["dumpEmoji"],
    )

    alerter = BinancePumpAndDumpAlerter(
        api_url=config["apiUrl"],
        watchlist=[] if "watchlist" not in config else config["watchlist"],
        blacklist=[] if "blacklist" not in config else config["blacklist"],
        pairs_of_interest=config["pairsOfInterest"],
        chart_intervals=config["chartIntervals"],
        outlier_intervals=config["outlierIntervals"],
        top_report_intervals=config["topReportIntervals"],
        extract_interval=ConversionUtils.duration_to_seconds(config["extractInterval"]),
        retry_interval=ConversionUtils.duration_to_seconds(
            config["priceRetryInterval"]
        ),
        reset_interval=ConversionUtils.duration_to_seconds(config["resetInterval"]),
        top_pump_enabled=config["topPumpEnabled"],
        top_dump_enabled=config["topDumpEnabled"],
        additional_statistics_enabled=config["additionalStatsEnabled"],
        no_of_reported_coins=config["noOfReportedCoins"],
        dump_enabled=config["dumpEnabled"],
        check_new_listing_enabled=config["checkNewListingEnabled"],
        top_report_nearest_hour=config["topReportNearestHour"],
        telegram=telegram,
        report_generator=reporter,
    )

    alerter.run()


if __name__ == "__main__":
    main()
