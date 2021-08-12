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
        top_emoji="\U0001F3C6",  # 🏆
        news_emoji="\U0001F4F0",  # 📰
    ):

        self.token = token
        self.chat_id = chat_id
        self.alert_chat_id = alert_chat_id
        self.retry_interval = retry_interval

        self.bot_emoji = bot_emoji
        self.top_emoji = top_emoji
        self.news_emoji = news_emoji

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

                self.bot.send_message(
                    chat_id=self.chat_id if not is_alert_chat else self.alert_chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
                break
            except Exception as e:
                self.logger.error(
                    "Error sending message with Telegram bot. Message: %s RetryInterval: %s Exception: %s.",
                    message,
                    self.retry_interval,
                    e,
                    exc_info=True,
                )
                sleep(self.retry_interval)

    def send_generic_message(self, message, args=None, is_alert_chat=False):
        if args is not None:
            message = message.format(args)
        self.send_message(self.bot_emoji + " " + message, is_alert_chat)

    def send_report_message(self, message, args=None, is_alert_chat=False):
        if args is not None:
            message = message.format(args)
        self.send_message(self.top_emoji + " " + message, is_alert_chat)

    def send_news_message(self, message, args=None, is_alert_chat=False):
        if args is not None:
            message = message.format(args)
        self.send_message(self.news_emoji + " " + message, is_alert_chat)
