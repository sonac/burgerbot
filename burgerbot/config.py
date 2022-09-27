import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

CHATS_FILE = "data/chats.json"
SERVICES_FILE = "data/services.json"
REFRESH_INTERVAL = (
    180  # minimum of 3 minutes is considered acceptable by berlin.de staff
)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
TELEGRAM_API_KEY = os.environ.get("TELEGRAM_API_KEY")
BOT_EMAIL = os.environ.get("BOT_EMAIL")
BOT_ID = os.environ.get("BOT_ID")


class MetaConfig(type):
    @property
    def chats_file(cls):
        return CHATS_FILE

    @property
    def services_file(cls):
        return SERVICES_FILE

    @property
    def refresh_interval(cls):
        return REFRESH_INTERVAL

    @property
    def log_level(cls):
        return LOG_LEVEL

    @property
    def telegram_api_key(cls):
        if TELEGRAM_API_KEY is None:
            error = Exception("TELEGRAM_API_KEY is not set")
            logging.exception(error)
            raise error

        return TELEGRAM_API_KEY

    @property
    def bot_email(cls):
        if BOT_EMAIL is None:
            error = Exception("BOT_EMAIL is not set")
            logging.exception(error)
            raise error

        return BOT_EMAIL

    @property
    def bot_id(cls):
        if BOT_ID is None:
            error = Exception("BOT_ID is not set")
            logging.exception(error)
            raise error

        return BOT_ID


class Config(metaclass=MetaConfig):
    pass
