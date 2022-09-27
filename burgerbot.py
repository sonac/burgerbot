#!/usr/bin/env python3

import json
import logging
import os
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from parser import Parser, Slot
from typing import Any, Dict, List

from telegram import ParseMode
from telegram.ext import CommandHandler, Updater
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from config import Config
from fetcher import Fetcher

service_map = {
    120335: "Abmeldung einer Wohnung",
    120686: "Anmeldung",
    120701: "Personalausweis beantragen",
    120702: "Meldebescheinigung beantragen",
    120703: "Reisepass beantragen",
    120914: "Zulassung eines Fahrzeuges mit auswärtigem Kennzeichen mit Halterwechsel",
    121469: "Kinderreisepass beantragen / verlängern / aktualisieren",
    121598: "Fahrerlaubnis - Umschreibung einer ausländischen Fahrerlaubnis aus einem EU-/EWR-Staat",
    121627: "Fahrerlaubnis - Ersterteilung beantragen",
    121701: "Beglaubigung von Kopien",
    121921: "Gewerbeanmeldung",
    318998: "Einbürgerung - Verleihung der deutschen Staatsangehörigkeit beantragen",
    324280: "Niederlassungserlaubnis oder Erlaubnis",
    326798: "Blaue Karte EU auf einen neuen Pass übertragen",
    327537: "Fahrerlaubnis - Umschreibung einer ausländischen",
}


@dataclass
class Message:
    message: str
    ts: int  # timestamp of adding msg to cache in seconds


@dataclass
class User:
    chat_id: int
    services: List[int]

    def __init__(self, chat_id, services=[]) -> None:
        self.chat_id = chat_id
        self.services = services

    def marshall_user(self) -> dict[str, Any]:
        self.services = list(
            set([s for s in self.services if s in list(service_map.keys())])
        )
        return asdict(self)


class Bot:
    def __init__(self, bot_email: str, bot_id: str, telegram_api_key: str) -> None:
        self.updater = Updater(telegram_api_key)
        self.__init_chats()
        self.users = self.__get_chats()
        self.parser = Parser(Fetcher(bot_email=bot_email, bot_id=bot_id))
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_handler(CommandHandler("help", self.__help))
        self.dispatcher.add_handler(CommandHandler("start", self.__start))
        self.dispatcher.add_handler(CommandHandler("stop", self.__stop))
        self.dispatcher.add_handler(CommandHandler("add_service", self.__add_service))
        self.dispatcher.add_handler(
            CommandHandler("remove_service", self.__remove_service)
        )
        self.dispatcher.add_handler(CommandHandler("my_services", self.__my_services))
        self.dispatcher.add_handler(CommandHandler("services", self.__services))
        self.cache: List[Message] = []

    def __get_uq_services(self) -> List[int]:
        services: List[int] = []
        for u in self.users:
            services.extend(u.services)
        services = list(filter(lambda x: x in service_map.keys(), services))
        return list(set(services))

    def __init_chats(self) -> None:
        if not os.path.exists(Config.chats_file):
            with open(Config.chats_file, "w") as f:
                f.write("[]")

    def __get_chats(self) -> List[User]:
        with open(Config.chats_file, "r") as f:
            users = [User(u["chat_id"], u["services"]) for u in json.load(f)]
            f.close()
            print(users)
            return users

    def __persist_chats(self) -> None:
        with open(Config.chats_file, "w") as f:
            json.dump([u.marshall_user() for u in self.users], f)
            f.close()

    def __add_chat(self, chat_id: int) -> None:
        if chat_id not in [u.chat_id for u in self.users]:
            logging.info("adding new user")
            self.users.append(User(chat_id))
            self.__persist_chats()

    def __remove_chat(self, chat_id: int) -> None:
        logging.info("removing the chat " + str(chat_id))
        self.users = [u for u in self.users if u.chat_id != chat_id]
        self.__persist_chats()

    def __services(self, update: Update, _: CallbackContext) -> None:
        if update.message is None:
            logging.info("update.message is None, bailing early")
            return

        services_text = ""
        for k, v in service_map.items():
            services_text += f"{k} - {v}\n"
        update.message.reply_text("Available services:\n" + services_text)

    def __help(self, update: Update, _: CallbackContext) -> None:
        if update.message is None:
            logging.info("update.message is None, bailing early")
            return

        try:
            update.message.reply_text(
                """
/start - start the bot
/stop - stop the bot
/add_service <service_id> - add service to your list
/remove_service <service_id> - remove service from your list
/my_services - view services on your list
/services - list of available services
"""
            )
        except Exception as e:
            logging.error(e)

    def __start(self, update: Update, _: CallbackContext) -> None:
        if update.message is None:
            logging.info("update.message is None, bailing early")
            return

        self.__add_chat(update.message.chat_id)
        logging.info(f"got new user with id {update.message.chat_id}")
        update.message.reply_text(
            "Welcome to BurgerBot. When there will be slot - you will receive notification. To get information about usage - type /help. To stop it - just type /stop"
        )

    def __stop(self, update: Update, _: CallbackContext) -> None:
        if update.message is None:
            logging.info("update.message is None, bailing early")
            return

        self.__remove_chat(update.message.chat_id)
        update.message.reply_text("Thanks for using me! Bye!")

    def __my_services(self, update: Update, _: CallbackContext) -> None:
        if update.message is None:
            logging.info("update.message is None, bailing early")
            return

        try:
            service_ids = set(
                service_id
                for u in self.users
                for service_id in u.services
                if u.chat_id == update.message.chat_id
            )
            msg = (
                "\n".join([f" - {service_id}" for service_id in service_ids])
                or " - (none)"
            )
            update.message.reply_text(
                "The following services are on your list:\n" + msg
            )
        except Exception as e:
            logging.error(e)

    def __add_service(self, update: Update, _: CallbackContext) -> None:
        if update.message is None:
            logging.info("update.message is None, bailing early")
            return

        if update.message.text is None:
            logging.info("update.message.text is None, bailing early")
            return

        logging.info(f"adding service {update.message}")
        try:
            service_id = int(update.message.text.split(" ")[1])

            if service_id not in service_map.keys():
                update.message.reply_text("Service not found")
                return

            for u in self.users:
                if u.chat_id == update.message.chat_id:
                    u.services.append(service_id)
                    self.__persist_chats()
                    break

            update.message.reply_text("Service added")
        except Exception as e:
            update.message.reply_text(
                "Failed to add service, have you specified the service id?"
            )
            logging.error(e)

    def __remove_service(self, update: Update, _: CallbackContext) -> None:
        if update.message is None:
            logging.info("update.message is None, bailing early")
            return

        if update.message.text is None:
            logging.info("update.message.text is None, bailing early")
            return

        logging.info(f"removing service {update.message}")
        try:
            service_id = int(update.message.text.split(" ")[1])
            for u in self.users:
                if u.chat_id == update.message.chat_id:
                    u.services.remove(int(service_id))
                    self.__persist_chats()
                    break
            update.message.reply_text("Service removed")
        except IndexError:
            update.message.reply_text(
                "Wrong usage. Please type '/remove_service 123456'"
            )

    def __poll(self) -> None:
        try:
            self.updater.start_polling()
        except Exception as e:
            logging.warning("got error during polling, retrying: %s", e)
            return self.__poll()

    def __parse(self) -> None:
        while True:
            logging.debug("starting parse run")
            services = self.__get_uq_services()
            slots = self.parser.parse(services)

            users_to_notify: Dict[User, List[Slot]] = {}

            for slot in slots:
                if self.__msg_in_cache(slot.result.url):
                    logging.info(
                        "Notification is cached already. Do not repeat sending"
                    )
                    continue

                self.__add_msg_to_cache(slot.result.url)

                users = [u for u in self.users if slot.service.id in u.services]

                for user in users:
                    if user not in users_to_notify:
                        users_to_notify[user] = []
                    users_to_notify[user].append(slot)

            for user, slots in users_to_notify.items():
                self.__send_message(user, slots)

            self.__clear_cache()
            time.sleep(Config.refresh_interval)

    def __build_service_markdown(self, service: int, slots: List[Slot]) -> str:
        slots_for_service = [s for s in slots if s.service.id == service]
        slots_for_service.sort(key=lambda x: x.result.date)

        slot_markdowns: List[str] = []

        for slot in slots_for_service:
            slot_markdowns.append(
                f"- [{self.__date_from_msg(slot.result.date)}]({slot.result.url})"
            )

        slot_markdown = "\n".join(slot_markdowns)

        service_markdown: str = f"*{service_map[service]}*\n\n{slot_markdown}"

        return service_markdown

    def __send_message(self, user: User, slots: List[Slot]) -> None:
        services_markdowns = [
            self.__build_service_markdown(service, slots) for service in user.services
        ]
        services_markdown = "\n\n".join(services_markdowns)
        markdown = f"""
Available appointments found!

{services_markdown}
        """

        logging.debug(f"sending msg to {str(user.chat_id)}")
        try:
            self.updater.bot.send_message(
                chat_id=user.chat_id, text=markdown, parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            if (
                "bot was blocked by the user" in e.__str__()
                or "user is deactivated" in e.__str__()
            ):
                logging.info("removing since user blocked bot or user was deactivated")
                self.__remove_chat(user.chat_id)
            else:
                logging.warning("error sending message: %s", e)

    def __msg_in_cache(self, msg: str) -> bool:
        for m in self.cache:
            if m.message == msg:
                return True
        return False

    def __add_msg_to_cache(self, msg: str) -> None:
        self.cache.append(Message(msg, int(time.time())))

    def __clear_cache(self) -> None:
        cur_ts = int(time.time())
        if len(self.cache) > 0:
            new_cache = [m for m in self.cache if (cur_ts - m.ts) < 300]

            if len(self.cache) != len(new_cache):
                logging.info("clearing some messages from cache")
                self.cache = new_cache

    def __date_from_msg(self, date: datetime) -> str:
        return date.strftime("%d %B")

    def start(self) -> None:
        logging.info("starting bot")
        poll_task = threading.Thread(target=self.__poll)
        parse_task = threading.Thread(target=self.__parse)
        parse_task.start()
        poll_task.start()
        parse_task.join()
        poll_task.join()


def main() -> None:
    bot = Bot(
        telegram_api_key=Config.telegram_api_key,
        bot_email=Config.bot_email,
        bot_id=Config.bot_id,
    )
    bot.start()


if __name__ == "__main__":
    log_level = Config.log_level
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)-5.5s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    main()
