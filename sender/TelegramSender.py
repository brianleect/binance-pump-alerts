import logging

from concurrent.futures import ThreadPoolExecutor
from telegram import Bot, ParseMode
from telegram.error import RetryAfter
from telegram.utils.request import Request
from time import sleep


class TelegramSender:
    def __init__(
        self,
        token,
        chat_id,
        alert_chat_id=0,
        bot_emoji="\U0001F916",  # 🤖
        top_emoji="\U0001F3C6",  # 🏆
        news_emoji="\U0001F4F0",  # 📰
    ):

        self.token = token
        self.chat_id = chat_id
        self.alert_chat_id = alert_chat_id

        self.bot_emoji = bot_emoji
        self.top_emoji = top_emoji
        self.news_emoji = news_emoji

        self.telegram_executor = ThreadPoolExecutor(max_workers=3)

        self.request = Request(con_pool_size=3)
        self.bot = Bot(self.token, request=self.request)

        self.logger = logging.getLogger("telegram-sender")

    def is_alert_chat_enabled(self):
        return self.alert_chat_id != 0 and self.alert_chat_id != self.chat_id

    def send_message(self, message, is_alert_chat=False):
        chat_id = self.chat_id if not is_alert_chat else self.alert_chat_id

        def push_message(bot, chat_id, message):
            self.logger.info(message)

            try:
                bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            except RetryAfter as e:
                self.logger.error(
                    "Flood limit is exceeded. Sleep {} seconds.", e.retry_after
                )
                sleep(e.retry_after)
                # Resend message to the queue
                self.send_message(message, is_alert_chat)
            except Exception as e:
                self.logger.error(str(e))

        self.telegram_executor.submit(
            lambda p: push_message(*p), (self.bot, chat_id, message)
        )

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
