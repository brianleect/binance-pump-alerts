import logging
from telegram import Bot, ParseMode
from time import sleep


class TelegramSender:
    def __init__(
        self,
        token,
        chat_id,
        alert_chat_id=0,
        retry_interval=2,
        bot_emoji="\U0001F916",  # 🤖
        pump_emoji="\U0001F7E2",  # 🟢
        dump_emoji="\U0001F534",  # 🔴
        top_emoji="\U0001F3C6",  # 🏆
        new_listing_emoji="\U0001F4F0",  # 📰
    ):

        self.token = token
        self.chat_id = chat_id
        self.alert_chat_id = alert_chat_id
        self.retry_interval = retry_interval

        self.bot_emoji = bot_emoji
        self.pump_emoji = pump_emoji
        self.dump_emoji = dump_emoji
        self.top_emoji = top_emoji
        self.new_listing_emoji = new_listing_emoji

        self.logger = logging.getLogger("telegram-sender")

        # Initialize telegram bot
        try:
            self.bot = Bot(token=token)
        except Exception as e:
            self.logger.error("Error initializing Telegram bot. Exception: %s.", e)
            quit()

    def is_alert_chat_enabled(self):
        return self.alert_chat_id != 0 and self.alert_chat_id != self.chat_id

    def send_message(self, message, is_alert_chat=False):
        while True:
            try:
                self.logger.debug(message)

                self.bot.sendMessage(
                    chat_id=self.chat_id if not is_alert_chat else self.alert_chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                )
                break
            except Exception as e:
                self.logger.error(
                    "Error sending message with Telegram bot. Message: %s RetryInterval: %s. Exception: %s",
                    message,
                    self.retry_interval,
                    e,
                    exc_info=True,
                )
                sleep(self.retry_interval)

    def send_generic_message(self, message, args, is_alert_chat=False):
        self.send_message(self.bot_emoji + " " + message.format(args), is_alert_chat)

    def send_interval_message(self, message, is_alert_chat=False):
        self.send_message(self.top_emoji + " " + message, is_alert_chat)

    def send_new_listing_message(self, symbols_to_add, is_alert_chat=False):
        message = """{0} *New Listings*
                     {1} new pairs found, adding to monitored list.
        
                     *Adding Pairs:*
                     """
        for symbol in symbols_to_add:
            message += "- _{}\n".format(symbol)

        message.format(self.new_listing_emoji, len(symbols_to_add), symbols_to_add)
        self.send_message(message, is_alert_chat)

    def send_pump_message(self, interval, symbol, change, price, is_alert_chat=False):
        self.send_message(
            "{0} *[{1} Interval] {2}* | Change: _{3:.3f}%_ | Price: _{4:.10f}_".format(
                self.pump_emoji, interval, symbol, change * 100, price
            ),
            is_alert_chat,
        )

    def send_dump_message(self, interval, symbol, change, price, is_alert_chat=False):
        self.send_message(
            "{0} *[{1} Interval] {2}* | Change: _{3:.3f}%_ | Price: _{4:.10f}_".format(
                self.dump_emoji, interval, symbol, change * 100, price
            ),
            is_alert_chat,
        )
