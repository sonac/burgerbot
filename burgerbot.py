#!/usr/bin/env python

import time
import os
import json
import threading
import logging
import sys
from dataclasses import dataclass, asdict
from typing import Any, List
from datetime import datetime

from telegram import ParseMode
from telegram.ext import CommandHandler, Updater
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from parser import Parser, Slot, build_url


CHATS_FILE = "chats.json"
ua_url = "https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=1&dienstleister=330857&anliegen[]=330869&herkunft=1"
register_prefix = "https://service.berlin.de"

service_map = {
    120335: "Abmeldung einer Wohnung",
    120686: "Anmeldung",
    120691: "Verpflichtungserklärung für einen kurzen Aufenthalt",
    120697: "Änderung/Wechsel der Hauptwohnung",
    120701: "Personalausweis beantragen",
    120702: "Meldebescheinigung",
    120703: "Reisepass beantragen",
    120914: "Zulassung eines Fahrzeuges mit auswärtigem Kennzeichen mit Halterwechsel",
    121469: "Kinderreisepass beantragen / verlängern / aktualisieren",
    121598: "Fahrerlaubnis Umschreibung einer ausländischen Fahrerlaubnis aus einem EU\\-/EWR\\-Staat",
    121616: "Führerschein Kartenführerschein umtauschen",
    121627: "Fahrerlaubnis Ersterteilung beantragen",
    121701: "Beglaubigung von Kopien",
    121921: "Gewerbeanmeldung",
    305244: "Aufenthaltserlaubnis zum Studium",
    318998: "Einbürgerung Verleihung der deutschen Staatsangehörigkeit beantragen",
    324269: "Aufenthaltserlaubnis für im Bundesgebiet geborene Kinder \\- Erteilung",
    324280: "Niederlassungserlaubnis oder Erlaubnis zum Daueraufenthalt\\-EU auf einen neuen Pass übertragen",
    326556: "Niederlassungserlaubnis für Inhaber einer Blauen Karte EU",
    326798: "Blaue Karte EU auf einen neuen Pass übertragen",
    327537: "Fahrerlaubnis Umschreibung einer ausländischen Fahrerlaubnis aus einem Nicht\\-EU/EWR\\-Land \\(Drittstaat/Anlage 11\\)",
    329328: "Aufenthaltserlaubnis für Fachkräfte mit akademischer Ausbildung",
}


@dataclass
class Message:
    message: str
    ts: int  # timestamp of adding msg to cache in seconds


@dataclass
class User:
    chat_id: int
    services: List[int]

    def __init__(self, chat_id, services=[120686]):
        self.chat_id = chat_id
        self.services = services if len(services) > 0 else [120686]

    def marshall_user(self) -> dict[str, Any]:
        self.services = list(
            set([s for s in self.services if s in list(service_map.keys())])
        )
        return asdict(self)


class Bot:
    def __init__(self) -> None:
        self.updater = Updater(os.environ["TELEGRAM_API_KEY"])
        self.__init_chats()
        self.users = self.__get_chats()
        self.parser = Parser()
        self.dispatcher = self.updater.dispatcher
        assert self.dispatcher is not None
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
        self.exit = threading.Event()

    def __get_uq_services(self) -> set[int]:
        return {
            service
            for user in self.users.values()
            for service in user.services
            if service in service_map
        }

    def __init_chats(self) -> None:
        if not os.path.exists(CHATS_FILE):
            with open(CHATS_FILE, "w") as f:
                f.write("[]")

    def __get_chats(self) -> dict[int, User]:
        with open(CHATS_FILE, "r") as f:
            users = [User(u["chat_id"], u["services"]) for u in json.load(f)]
            logging.info(users)
            return {u.chat_id: u for u in users}

    def __persist_chats(self) -> None:
        with open(CHATS_FILE, "w") as f:
            marshalled_users = [u.marshall_user() for u in self.users.values()]
            json.dump(marshalled_users, f)

    def __add_chat(self, chat_id: int) -> None:
        if chat_id in self.users:
            logging.info(f"attempted to add user {chat_id} but it already exists")
            return

        logging.info(f"adding new user {chat_id}")
        self.users[chat_id] = User(chat_id)
        self.__persist_chats()

    def __remove_chat(self, chat_id: int) -> None:
        logging.info("removing the chat " + str(chat_id))
        self.users.pop(chat_id)
        self.__persist_chats()

    def __services(self, update: Update, _: CallbackContext) -> None:
        services_text = ""
        for k, v in service_map.items():
            services_text += f"{k} - {v}\n"
        update.message.reply_text("Available services:\n" + services_text)

    def __help(self, update: Update, _: CallbackContext) -> None:
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
            logging.error(f"error occured during help reply, {e}")

    def __start(self, update: Update, _: CallbackContext) -> None:
        self.__add_chat(update.message.chat_id)
        logging.info(f"got new user with id {update.message.chat_id}")
        update.message.reply_text(
            "Welcome to BurgerBot. When there will be slot - you will receive notification. To get information about usage - type /help. To stop it - just type /stop"
        )

    def __stop(self, update: Update, _: CallbackContext) -> None:
        self.__remove_chat(update.message.chat_id)
        update.message.reply_text("Thanks for using me! Bye!")

    def __my_services(self, update: Update, _: CallbackContext) -> None:
        chat_id = update.message.chat_id
        try:
            user = self.users[chat_id]
            service_ids = set(user.services)
            msg = (
                "\n".join([f" - {service_id}" for service_id in service_ids])
                or " - (none)"
            )
            update.message.reply_text(
                "The following services are on your list:\n" + msg
            )
        except KeyError:
            logging.warning(f"user {chat_id} not found")
        except Exception as e:
            logging.error(f"error occured when listing user services, {e}")

    def __add_service(self, update: Update, _: CallbackContext) -> None:
        logging.info(f"adding service {update.message}")
        chat_id = update.message.chat_id
        try:
            user = self.users[chat_id]
            service_id = int(update.message.text.split(" ")[1])
            user.services.append(service_id)
            self.__persist_chats()
            update.message.reply_text("Service added")
        except KeyError:
            logging.warning(f"user {chat_id} not found")
        except Exception as e:
            update.message.reply_text(
                "Failed to add service, have you specified the service id?"
            )
            logging.error(f"error occured when adding new service {e}")

    def __remove_service(self, update: Update, _: CallbackContext) -> None:
        logging.info(f"removing service {update.message}")
        chat_id = update.message.chat_id
        try:
            user = self.users[chat_id]
            service_id = int(update.message.text.split(" ")[1])
            user.services.remove(service_id)
            self.__persist_chats()
            update.message.reply_text("Service removed")
        except KeyError:
            logging.warning(f"user {chat_id} not found")
        except IndexError:
            update.message.reply_text(
                "Wrong usage. Please type '/remove_service 123456'"
            )

    def __poll(self) -> None:
        try:
            self.updater.start_polling()
        except Exception as e:
            logging.warn(e)
            logging.warn("got error during polling, retying")
            return self.__poll()

    def __parse(self) -> None:
        while not self.exit.is_set():
            services = self.__get_uq_services()
            logging.info(f"services are: {services}")
            slots = self.parser.parse(services)
            for slot in slots:
                self.__send_message(slot)
            self.exit.wait(30)

    def __send_message(self, slot: Slot) -> None:
        if self.__msg_in_cache(slot.msg):
            logging.info("Notification is cached already. Do not repeat sending")
            return
        self.__add_msg_to_cache(slot.msg)
        md_msg = f"There are slots on {self.__date_from_msg(slot.msg)} available for booking for {service_map[slot.service_id]}, click [here]({build_url(slot.service_id)}) to check it out"
        users = [u for u in self.users.values() if slot.service_id in u.services]
        for u in users:
            logging.debug(f"sending msg to {str(u.chat_id)}")
            try:
                self.updater.bot.send_message(
                    chat_id=u.chat_id, text=md_msg, parse_mode=ParseMode.MARKDOWN_V2
                )
            except Exception as e:
                if (
                    "bot was blocked by the user" in e.__str__()
                    or "user is deactivated" in e.__str__()
                ):
                    logging.info(
                        "removing since user blocked bot or user was deactivated"
                    )
                    self.__remove_chat(u.chat_id)
                else:
                    logging.exception(f"error occured when sending message '{md_msg}")
        self.__clear_cache()

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
            logging.info("clearing some messages from cache")
            self.cache = [m for m in self.cache if (cur_ts - m.ts) < 300]

    def __date_from_msg(self, msg: str) -> str:
        msg_arr = msg.split("/")
        logging.info(msg)
        ts = (
            int(msg_arr[len(msg_arr) - 2]) + 7200
        )  # adding two hours to match Berlin TZ with UTC
        return datetime.fromtimestamp(ts).strftime("%d %B")

    def start(self) -> None:
        logging.info("starting bot")
        self.exit.clear()
        poll_task = threading.Thread(target=self.__poll)
        parse_task = threading.Thread(target=self.__parse)
        parse_task.start()
        poll_task.start()
        try:
            self.exit.wait()
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt, exiting...")
            self.exit.set()
            self.updater.stop()
            parse_task.join()
            poll_task.join()


def main() -> None:
    bot = Bot()
    bot.start()


if __name__ == "__main__":
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)-5.5s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    main()
