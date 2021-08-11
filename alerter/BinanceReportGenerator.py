import logging


class BinanceReportGenerator:
    def __init__(
        self,
        pump_emoji,
        dump_emoji,
        telegram,
    ):
        self.pump_emoji = pump_emoji
        self.dump_emoji = dump_emoji
        self.telegram = telegram

    def send_summarized_pump_dump_message(
        self,
        asset,
        chart_intervals,
        dump_enabled=True,
    ):
        for interval in chart_intervals:

            change = asset[interval]["change_alert"]

            # TODO: Send summarized alert messages to reduce
            if change > 0:
                self.telegram.send_pump_message(
                    interval,
                    asset["symbol"],
                    change,
                    asset["price"][-1],
                )

            if change < 0 and dump_enabled:
                self.telegram.send_dump_message(
                    interval,
                    asset["symbol"],
                    change,
                    asset["price"][-1],
                )

    def send_top_pump_dump_statistics_report(
        self,
        assets,
        interval,
        top_pump_enabled=True,
        top_dump_enabled=True,
        additional_stats_enabled=True,
        no_of_reported_coins=5,
    ):
        message = "*[{0} Interval]*\n\n".format(interval)

        if top_pump_enabled:
            # TODO: Check if sorting still works since it is stored as asset[interval]['change_alert'] or asset[interval]['change_top_alert']
            pump_sorted_list = sorted(assets, key=lambda i: i[interval], reverse=True)[
                0:no_of_reported_coins
            ]

            message += "*Top {0} Pumps*\n".format(no_of_reported_coins)

            for asset in pump_sorted_list:
                message += "- {0}: _{1:.2f}_%\n".format(
                    asset["symbol"], asset[interval] * 100
                )
            message += "\n"

        if top_dump_enabled:
            # TODO: Check if sorting still works since it is stored as asset[interval]['change_alert'] or asset[interval]['change_top_alert']
            dump_sorted_list = sorted(assets, key=lambda i: i[interval])[
                0:no_of_reported_coins
            ]

            message += "*Top {0} Dumps*\n".format(no_of_reported_coins)

            for asset in dump_sorted_list:
                message += "- {0}: _{1:.2f}_%\n".format(
                    asset["symbol"], asset[interval] * 100
                )

        if additional_stats_enabled:
            if top_pump_enabled or top_dump_enabled:
                message += "\n"
            message += self.generate_additional_statistics_report(assets, interval)

        self.telegram.send_interval_message(message, is_alert_chat=True)

    def generate_additional_statistics_report(self, assets, interval):
        up = 0
        down = 0
        sum_change = 0

        for asset in assets:
            if asset[interval] > 0:
                up += 1
            elif asset[interval] < 0:
                down += 1

            sum_change += asset[interval]

        avg_change = sum_change / len(assets)

        return "*Average Change:* {0:.2f}%\n {1} {2} / {3} {4}".format(
            avg_change * 100,
            self.pump_emoji,
            up,
            self.dump_emoji,
            down,
        )
