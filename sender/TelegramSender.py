import logging
from telegram import Bot, ParseMode
from time import sleep


class TelegramSender:
    def __init__(
        self,
        token,
        retryInterval,
        chatId,
        alertChatId,
        botEmoji="\U0001F916",  # 🤖
        pumpEmoji="\U0001F7E2",  # 🟢
        dumpEmoji="\U0001F534",  # 🔴
        tdpaEmoji="\U0001F3C6",  # 🏆
        newListingEmoji="\U0001F4F0",  # 📰
    ):

        self.token = token
        self.retryInterval = retryInterval
        self.chatId = chatId
        self.alertChatId = alertChatId

        self.botEmoji = botEmoji
        self.pumpEmoji = pumpEmoji
        self.dumpEmoji = dumpEmoji
        self.tdpaEmoji = tdpaEmoji
        self.newListingEmoji = newListingEmoji

        self.logger = logging.getLogger("telegram-sender")

        # Initialize telegram bot
        try:
            self.bot = Bot(token=token)
        except Exception as e:
            self.logger.error("Error initializing Telegram bot. Exception: %s.", e)
            quit()

    def sendMessage(self, message, isAlertChat=False):
        while True:
            try:
                self.logger.debug(message)

                self.bot.sendMessage(
                    chat_id=self.chatId if not isAlertChat else self.alertChatId,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                )
                break
            except Exception as e:
                self.logger.error(
                    "Error sending message with Telegram bot. Message: %s RetryInterval: %s. Exception: %s",
                    message,
                    self.retryInterval,
                    e,
                    exc_info=True,
                )
                sleep(self.retryInterval)

    def sendGenericMessage(self, message, args, isAlertChat=False):
        self.sendMessage(self.botEmoji + " " + message.format(args), isAlertChat)

    def sendIntervalMessage(self, message, isAlertChat=False):
        self.sendMessage(self.tdpaEmoji + " " + message, isAlertChat)

    def sendNewListingMessage(self, symbolsToAdd, isAlertChat=False):
        message = """{0} *New Listings*
                     {1} new pairs found, adding to monitored list.
        
                     *Adding Pairs:*
                     """
        for symbol in symbolsToAdd:
            message += "- _{}\n".format(symbol)

        message.format(self.newListingEmoji, len(symbolsToAdd), symbolsToAdd)
        self.sendMessage(message, isAlertChat)

    def sendPumpMessage(self, interval, symbol, change, price, isAlertChat=False):
        self.sendMessage(
            "{0} *[{1} Interval] {2}* | Change: _{3:.3f}%_ | Price: _{4:.10f}_".format(
                self.pumpEmoji, interval, symbol, change * 100, price
            ),
            isAlertChat,
        )

    def sendDumpMessage(self, interval, symbol, change, price, isAlertChat=False):
        self.sendMessage(
            "{0} *[{1} Interval] {2}* | Change: _{3:.3f}%_ | Price: _{4:.10f}_".format(
                self.dumpEmoji, interval, symbol, change * 100, price
            ),
            isAlertChat,
        )

    def sendTopPumpDumpStatisticsReport(
        self,
        assets,
        interval,
        topPumpEnabled=True,
        topDumpEnabled=True,
        additionalStatsEnabled=True,
        noOfReportedCoins=5,
    ):
        message = "*[{0} Interval]*\n\n".format(interval)

        if topPumpEnabled:
            pumpSortedList = sorted(assets, key=lambda i: i[interval], reverse=True)[
                0:noOfReportedCoins
            ]

            message += "*Top {0} Pumps*\n".format(noOfReportedCoins)

            for asset in pumpSortedList:
                message += "- {0}: _{1:.2f}_%\n".format(
                    asset["symbol"], asset[interval] * 100
                )
            message += "\n"

        if topDumpEnabled:
            dumpSortedList = sorted(assets, key=lambda i: i[interval])[
                0:noOfReportedCoins
            ]

            message += "*Top {0} Dumps*\n".format(noOfReportedCoins)

            for asset in dumpSortedList:
                message += "- {0}: _{1:.2f}_%\n".format(
                    asset["symbol"], asset[interval] * 100
                )

        if additionalStatsEnabled:
            if topPumpEnabled or topDumpEnabled:
                message += "\n"
            message += self.generateAdditionalStatisticsReport(assets, interval)

        self.sendIntervalMessage(message, isAlertChat=True)

    def generateAdditionalStatisticsReport(self, assets, interval):
        up = 0
        down = 0
        sumChange = 0

        for asset in assets:
            if asset[interval] > 0:
                up += 1
            elif asset[interval] < 0:
                down += 1

            sumChange += asset[interval]

        avgChange = sumChange / len(assets)

        return "*Average Change:* {0:.2f}%\n {1} {2} / {3} {4}".format(
            avgChange * 100,
            self.pumpEmoji,
            up,
            self.dumpEmoji,
            down,
        )
