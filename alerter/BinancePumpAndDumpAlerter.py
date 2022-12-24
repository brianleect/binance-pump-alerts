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
        blacklist,
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
        top_report_nearest_hour,
        telegram,
        report_generator,
    ):
        self.api_url = api_url
        self.watchlist = watchlist
        self.blacklist = blacklist
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

        self.logger = logging.getLogger("pump-and-dump-alerter")

        self.initial_time = int(time.time())
        nearest_hour = self.initial_time - (self.initial_time % 3600) + 3600
        self.logger.info(
            "Nearest hour is %i seconds away", nearest_hour - self.initial_time
        )

        self.chart_intervals = {}
        for interval in chart_intervals:
            self.chart_intervals[interval] = {}
            self.chart_intervals[interval][
                "value"
            ] = ConversionUtils.duration_to_seconds(interval)

        self.top_report_intervals = {}
        for interval in top_report_intervals:
            self.top_report_intervals[interval] = {}

            # Determine initial start time for TPD. Should conveniently solve original 0% issue together.
            if top_report_nearest_hour:
                self.top_report_intervals[interval]["start"] = nearest_hour
            else:
                self.top_report_intervals[interval]["start"] = self.initial_time

            self.top_report_intervals[interval][
                "value"
            ] = ConversionUtils.duration_to_seconds(interval)

    @staticmethod
    def extract_ticker_data(symbol, assets):
        for asset in assets:
            if asset["symbol"] == symbol:
                return asset

    @staticmethod
    def create_new_asset(symbol, chart_intervals):
        asset = {"symbol": symbol, "price": [], "volume": []}

        for interval in chart_intervals:
            asset[interval] = {}
            asset[interval]["change_current"] = 0
            asset[interval]["change_last"] = 0
            asset[interval]["change_volume"] = 0

        return asset

    def retrieve_exchange_assets(self, api_url):
        try:
            self.logger.debug(
                "Retrieving price information from the ticker. ApiUrl: %s.", api_url
            )
            return requests.get(api_url).json()
        except Exception as e:
            self.logger.error(
                "Issue occurred while getting prices. Error: %s.",
                e,
                exc_info=True,
            )
            sleep(5)  # Sleep 5s and try again
            return self.retrieve_exchange_assets(api_url)

    def is_symbol_valid(self, symbol, watchlist, blacklist, pairs_of_interest):
        # Filter symbols in watchlist if set - This disables the pairsOfInterest feature
        if len(watchlist) > 0:
            if symbol not in watchlist:
                self.logger.debug("Ignoring symbol not in watchlist: %s.", symbol)
                return False
            return True

        # Filter symbols in blacklist if set - This DOES NOT IMPACT the pairsOfInterest feature
        if len(blacklist) > 0:
            if symbol in blacklist:
                self.logger.info(
                    "Ignoring symbol found in blacklist: %s.", symbol)
                return False

        # Filter pairsOfInterest to reduce the noise. E.g. BUSD, USDT, ETH, BTC
        is_in_pairs_of_interest = False
        for pair in pairs_of_interest:
            if symbol.endswith(pair):
                is_in_pairs_of_interest = True
                break

        if not is_in_pairs_of_interest:
            self.logger.debug("Ignoring symbol not in pairsOfInterests: %s.", symbol)
            return False

        # Filter leverage symbols
        for pair in pairs_of_interest:
            coin = symbol.replace(pair, "")
            if (
                coin.endswith("UP")
                or coin.endswith("DOWN")
                or coin.endswith("BULL")
                or coin.endswith("BEAR")
            ):
                self.logger.debug("Ignoring leverage symbol: %s.", symbol)
                return False

        return True

    def filter_and_convert_assets(
        self, exchange_assets, watchlist, blacklist, pairs_of_interest, chart_intervals
    ):
        filtered_assets = []

        for exchange_asset in exchange_assets:
            symbol = exchange_asset["symbol"]

            if self.is_symbol_valid(symbol, watchlist, blacklist, pairs_of_interest):
                filtered_assets.append(self.create_new_asset(symbol, chart_intervals))
                self.logger.info("Adding symbol: %s.", symbol)

        return filtered_assets

    def update_all_monitored_assets_and_send_news_messages(
        self,
        monitored_assets,
        exchange_assets,
        current_time,
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
                chart_intervals,
                extract_interval,
            )

            self.report_generator.send_pump_dump_message(
                asset,
                chart_intervals,
                outlier_intervals,
                current_time,
                dump_enabled,
            )

    def calculate_asset_change(
        self,
        asset,
        chart_intervals,
        extract_interval,
    ):
        asset_length = len(asset["price"])

        for interval in chart_intervals:

            data_points = chart_intervals[interval]["value"] // extract_interval

            # If data is not available yet after restart for interval, stop here.
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
            self.logger.debug(
                "Calculated asset: %s for interval: %s with change: %s",
                asset["symbol"],
                interval,
                change,
            )

            # Set last change for next interval iteration
            asset[interval]["change_last"] = asset[interval]["change_current"]

            # Stores change for the current interval into asset dict.
            asset[interval]["change_current"] = change

        return asset

    def reset_prices_data_when_due(
        self,
        initial_time,
        current_time,
        reset_interval,
        extract_interval,
        assets,
        chart_intervals,
    ):
        if current_time - initial_time > reset_interval:

            message = "Emptying price data to prevent memory errors."
            self.logger.debug(message)
            self.telegram.send_generic_message(message, is_alert_chat=True)

            # Do not delete everything, only elements older than the last monitored interval
            lastInterval = "1s"
            for interval in chart_intervals:
                lastInterval = interval

            data_points = chart_intervals[lastInterval]["value"] // extract_interval

            for asset in assets:
                asset["price"] = asset["price"][-1 - data_points :]

            initial_time = current_time

        return initial_time

    def add_new_asset_listings(
        self,
        initial_assets,
        filtered_assets,
        exchange_assets,
        watchlist,
        blacklist,
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
            if self.is_symbol_valid(symbol, watchlist, blacklist, pairs_of_interest):
                filtered_symbols_to_add.append(symbol)
                filtered_assets.append(self.create_new_asset(symbol, chart_intervals))

        self.logger.debug("Filtered new listings found: %s.", filtered_symbols_to_add)

        if len(filtered_symbols_to_add) > 0:
            self.report_generator.send_new_listings(filtered_symbols_to_add)

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
                + 1
            ):
            
                # Update time for new trigger, rounded down to nearest interval. Avoid delay over time.
                top_report_intervals[interval]["start"] = current_time - (current_time % ConversionUtils.duration_to_seconds(interval))

                self.logger.debug(
                    "Sending out top pump dump report. Interval: %s.", interval
                )

                self.report_generator.send_top_pump_dump_statistics_report(
                    assets,
                    interval,
                    top_pump_enabled,
                    top_dump_enabled,
                    additional_stats_enabled,
                    no_of_reported_coins,
                )

    def run(self):

        initial_assets = self.retrieve_exchange_assets(self.api_url)

        filtered_assets = self.filter_and_convert_assets(
            initial_assets,
            self.watchlist,
            self.blacklist,
            self.pairs_of_interest,
            self.chart_intervals,
        )

        message = "*Bot has started.* Following _{0}_ pairs."
        self.telegram.send_generic_message(message, len(filtered_assets))
        if self.telegram.is_alert_chat_enabled():
            self.telegram.send_generic_message(
                message,
                len(filtered_assets),
                is_alert_chat=True,
            )

        while True:
            start_loop_time = time.time()
            loop_time = int(start_loop_time)

            exchange_assets = self.retrieve_exchange_assets(self.api_url)

            if self.check_new_listing_enabled:
                filtered_assets = self.add_new_asset_listings(
                    initial_assets,
                    filtered_assets,
                    exchange_assets,
                    self.watchlist,
                    self.blacklist,
                    self.pairs_of_interest,
                    self.chart_intervals,
                )
                # Reset initial exchange asset
                initial_assets = exchange_assets

            self.update_all_monitored_assets_and_send_news_messages(
                filtered_assets,
                exchange_assets,
                loop_time,
                self.dump_enabled,
                self.chart_intervals,
                self.extract_interval,
                self.outlier_intervals,
            )

            self.check_and_send_top_pump_dump_statistics_report(
                filtered_assets,
                loop_time,
                self.top_report_intervals,
                self.top_pump_enabled,
                self.top_dump_enabled,
                self.additional_statistics_enabled,
                self.no_of_reported_coins,
            )

            self.initial_time = self.reset_prices_data_when_due(
                self.initial_time,
                loop_time,
                self.reset_interval,
                self.extract_interval,
                filtered_assets,
                self.chart_intervals,
            )

            # Sleeps for the remainder of 1s, or loops through if extraction takes longer
            end_loop_time = time.time()

            self.logger.info(
                "Extracting loop started at %d and finished at %d. Taking %f seconds.",
                start_loop_time,
                end_loop_time,
                end_loop_time - start_loop_time,
            )

            if end_loop_time < start_loop_time + self.extract_interval:
                sleep_time = start_loop_time + self.extract_interval - end_loop_time
                self.logger.debug("Now sleeping %f seconds.", sleep_time)
                sleep(sleep_time)
