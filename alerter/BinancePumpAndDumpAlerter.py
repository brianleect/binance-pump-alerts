import logging
import requests
import time

from time import sleep
from utils import ConversionUtils


class BinancePumpAndDumpAlerter:
    def __init__(
        self,
        api_url,
        watchlist,
        pairs_of_interest,
        chart_intervals,
        outlier_intervals,
        top_report_intervals,
        extract_interval,
        retry_interval,
        reset_interval,
        top_pump_enabled,
        top_dump_enabled,
        additional_statistics_enabled,
        no_of_reported_coins,
        dump_enabled,
        check_new_listing_enabled,
        telegram,
        report_generator,
    ):
        self.api_url = api_url
        self.watchlist = watchlist
        self.pairs_of_interest = pairs_of_interest
        self.outlier_intervals = outlier_intervals
        self.extract_interval = extract_interval
        self.retry_interval = retry_interval
        self.reset_interval = reset_interval
        self.top_pump_enabled = top_pump_enabled
        self.top_dump_enabled = top_dump_enabled
        self.additional_statistics_enabled = additional_statistics_enabled
        self.no_of_reported_coins = no_of_reported_coins
        self.dump_enabled = dump_enabled
        self.check_new_listing_enabled = check_new_listing_enabled
        self.telegram = telegram
        self.report_generator = report_generator

        self.initial_time = time.time()

        self.chart_intervals = {}
        for interval in chart_intervals:
            self.chart_intervals[interval] = {}
            self.chart_intervals[interval][
                "value"
            ] = ConversionUtils.duration_to_seconds(interval)

        self.top_report_intervals = {}
        for interval in top_report_intervals:
            self.top_report_intervals[interval] = {}
            self.top_report_intervals[interval]["start"] = self.initial_time
            self.top_report_intervals[interval][
                "value"
            ] = ConversionUtils.duration_to_seconds(interval)

        self.logger = logging.getLogger("pump-and-dump-alerter")

    @staticmethod
    def extract_ticker_data(symbol, assets):
        for asset in assets:
            if asset["symbol"] == symbol:
                return asset

    @staticmethod
    def create_new_asset(symbol, chart_intervals):
        asset = {"symbol": symbol, "price": []}

        for interval in chart_intervals:
            asset[interval] = {}
            asset[interval]["change_alert"] = 0
            asset[interval]["change_top_report"] = 0

        return asset

    def retrieve_exchange_assets(self, api_url, retry_interval):
        while True:
            try:
                self.logger.debug(
                    "Retrieving price information from the ticker. ApiUrl: %s.", api_url
                )
                return requests.get(api_url).json()
            except Exception as e:
                self.logger.error(
                    "Issue occurred while getting prices. Retrying in %ss. Error: %s.",
                    retry_interval,
                    e,
                    exc_info=True,
                )
                sleep(retry_interval)

    def is_symbol_valid(self, symbol, watchlist, pairs_of_interest):
        # Filter symbols not in watchlist if set
        if len(watchlist) > 0:
            if symbol not in watchlist:
                self.logger.debug("Ignoring symbol not in watchlist: %s.", symbol)
                return False

        # TODO: Make this filtering more stable. Leverage should be at the end of the first
        # part of the symbol, which needs to be in pairsOfInterest.

        # Removing leverage symbols
        if (
            ("UP" in symbol)
            or ("DOWN" in symbol)
            or ("BULL" in symbol)
            or ("BEAR" in symbol)
        ) and ("SUPER" not in symbol):
            self.logger.debug("Ignoring leverage symbol: %s.", symbol)
            return False

        # Filter pairsOfInterest to reduce the noise. E.g. BUSD, USDT, ETH, BTC
        if (
            symbol[-4:] not in pairs_of_interest
            and symbol[-3:] not in pairs_of_interest
        ):
            self.logger.debug("Ignoring symbol not in pairsOfInterests: %s.", symbol)
            return False

        return True

    def filter_and_convert_assets(
        self, exchange_assets, watchlist, pairs_of_interest, chart_intervals
    ):
        filtered_assets = []

        for exchange_asset in exchange_assets:
            symbol = exchange_asset["symbol"]

            if self.is_symbol_valid(symbol, watchlist, pairs_of_interest):
                filtered_assets.append(self.create_new_asset(symbol, chart_intervals))
                self.logger.info("Adding symbol: %s.", symbol)

        return filtered_assets

    def update_all_monitored_assets_and_send_alert_messages(
        self,
        monitored_assets,
        exchange_assets,
        dump_enabled,
        chart_intervals,
        extract_interval,
        outlier_intervals,
    ):
        for asset in monitored_assets:
            exchange_asset = self.extract_ticker_data(asset["symbol"], exchange_assets)
            asset["price"].append(float(exchange_asset["price"]))

            self.calculate_asset_change(
                asset,
                dump_enabled,
                chart_intervals,
                extract_interval,
                outlier_intervals,
            )

            self.report_generator.send_summarized_pump_dump_message(
                asset, chart_intervals, dump_enabled
            )

        return monitored_assets

    def calculate_asset_change(
        self,
        asset,
        dump_enabled,
        chart_intervals,
        extract_interval,
        outlier_intervals,
    ):
        asset_length = len(asset["price"])

        for interval in chart_intervals:

            self.logger.debug(
                "Calculate asset: %s with interval: %s", asset["symbol"], interval
            )

            data_points = int(chart_intervals[interval]["value"] / extract_interval)

            # If data is not avalilable yet after restart for interval, stop here.
            if data_points >= asset_length:
                self.logger.debug(
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
            asset[interval]["change_top_report"] = change

            if abs(change) >= outlier_intervals[interval]:
                asset[interval]["change_alert"] = change

        return asset

    def reset_prices_data_when_due(
        self,
        initial_time,
        current_time,
        reset_interval,
        assets,
    ):
        if current_time - initial_time > reset_interval:

            message = "Emptying price data to prevent memory errors."
            self.logger.debug(message)
            self.telegram.send_generic_message(message)

            # TODO: Do not delete everything, only elements older than the last monitored interval
            for asset in assets:
                asset["price"] = []

            initial_time = current_time

        return initial_time

    def add_new_asset_listings(
        self,
        initial_assets,
        filtered_assets,
        exchange_assets,
        watchlist,
        pairs_of_interest,
        chart_intervals,
    ):

        if len(initial_assets) >= len(exchange_assets):
            # If initial_assets has more than assets we just ignore it
            self.logger.debug("No new listing found.")
            return filtered_assets

        init_symbols = [asset["symbol"] for asset in initial_assets]
        retrieved_symbols_to_add = [
            exchange_asset["symbol"]
            for exchange_asset in exchange_assets
            if exchange_asset["symbol"] not in init_symbols
        ]

        self.logger.debug("New listings found: %s.", retrieved_symbols_to_add)

        filtered_symbols_to_add = []
        for symbol in retrieved_symbols_to_add:
            if self.is_symbol_valid(symbol, watchlist, pairs_of_interest):
                filtered_symbols_to_add.append(symbol)
                filtered_assets.append(self.create_new_asset(symbol, chart_intervals))

        self.logger.debug("Filtered new listings found: %s.", filtered_symbols_to_add)

        # Sends combined message
        self.telegram.send_new_listing_message(filtered_symbols_to_add)

        return filtered_assets

    def check_and_send_top_pump_dump_statistics_report(
        self,
        assets,
        current_time,
        top_report_intervals,
        top_pump_enabled,
        top_dump_enabled,
        additional_stats_enabled,
        no_of_reported_coins,
    ):

        for interval in top_report_intervals:
            if (
                current_time
                > top_report_intervals[interval]["start"]
                + top_report_intervals[interval]["value"]
            ):
                # Update time for new trigger
                top_report_intervals[interval]["start"] = current_time

                self.logger.debug(
                    "Sending out top pump dump report. Interval: %s.", interval
                )

                self.send_top_pump_dump_statistics_report(
                    assets,
                    interval,
                    top_pump_enabled,
                    top_dump_enabled,
                    additional_stats_enabled,
                    no_of_reported_coins,
                )

            return top_report_intervals

    def run(self):

        initial_assets = self.retrieve_exchange_assets(
            self.api_url, self.retry_interval
        )

        filtered_assets = self.filter_and_convert_assets(
            initial_assets,
            self.watchlist,
            self.pairs_of_interest,
            self.chart_intervals,
        )

        message = "*Bot has started.* Following _{0}_ pairs."
        self.telegram.send_generic_message(message, len(filtered_assets))
        if self.telegram.is_alert_chat_enabled:
            self.telegram.send_generic_message(
                message,
                len(filtered_assets),
                is_alert_chat=True,
            )

        while True:
            start_loop_time = time.time()

            self.initial_time = self.reset_prices_data_when_due(
                self.initial_time,
                start_loop_time,
                self.reset_interval,
                filtered_assets,
            )

            exchange_assets = self.retrieve_exchange_assets(
                self.api_url, self.retry_interval
            )

            if self.check_new_listing_enabled:
                filtered_assets = self.add_new_asset_listings(
                    initial_assets,
                    filtered_assets,
                    exchange_assets,
                    self.watchlist,
                    self.pairs_of_interest,
                    self.chart_intervals,
                )
                # Reset initial exchange asset
                initial_assets = exchange_assets

            filtered_assets = self.update_all_monitored_assets_and_send_alert_messages(
                filtered_assets,
                exchange_assets,
                self.dump_enabled,
                self.chart_intervals,
                self.extract_interval,
                self.outlier_intervals,
            )

            self.top_report_intervals = (
                self.check_and_send_top_pump_dump_statistics_report(
                    filtered_assets,
                    start_loop_time,
                    self.top_report_intervals,
                    self.top_pump_enabled,
                    self.top_dump_enabled,
                    self.additional_statistics_enabled,
                    self.no_of_reported_coins,
                )
            )

            # Sleeps for the remainder of 1s, or loops through if extraction takes longer
            end_loop_time = time.time()

            self.logger.info(
                "Extracting loop started at %d and finished at %d. It took %f seconds.",
                start_loop_time,
                end_loop_time,
                end_loop_time - start_loop_time,
            )

            if end_loop_time < start_loop_time + self.extract_interval:
                sleep_time = start_loop_time + self.extract_interval - end_loop_time
                self.logger.debug("Now sleeping %f seconds.", sleep_time)
                sleep(sleep_time)
