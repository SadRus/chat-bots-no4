from logging.handlers import RotatingFileHandler


class TelegramLogsHandler(RotatingFileHandler):

    def __init__(self, filename, tg_bot, chat_id, **kwargs):
        super().__init__(filename, **kwargs)
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        super().emit(record)
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)
