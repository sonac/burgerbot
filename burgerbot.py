import time
import os
import json
import threading
import logging
import sys
from dataclasses import dataclass
from typing import List
from datetime import datetime 

import requests
from bs4 import BeautifulSoup
from telegram import ParseMode
from telegram.ext import CommandHandler, Updater
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

url = 'https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=1&anliegen[]=120686&dienstleisterlist=122210,122217,327316,122219,327312,122227,327314,122231,327346,122243,327348,122252,329742,122260,329745,122262,329748,122254,329751,122271,327278,122273,327274,122277,327276,330436,122280,327294,122282,327290,122284,327292,327539,122291,327270,122285,327266,122286,327264,122296,327268,150230,329760,122301,327282,122297,327286,122294,327284,122312,329763,122314,329775,122304,327330,122311,327334,122309,327332,122281,327352,122279,329772,122276,327324,122274,327326,122267,329766,122246,327318,122251,327320,122257,327322,122208,327298,122226,327300&herkunft=http%3A%2F%2Fservice.berlin.de%2Fdienstleistung%2F120686%2F'
register_prefix = 'https://service.berlin.de'

@dataclass
class Message:
  message: str
  ts: int # timestamp of adding msg to cache in seconds

class Bot:
  def __init__(self) -> None:
    self.updater = Updater(os.environ["TELEGRAM_API_KEY"])
    self.__get_chats()
    self.dispatcher = self.updater.dispatcher
    self.dispatcher.add_handler(CommandHandler('start', self.__start))
    self.dispatcher.add_handler(CommandHandler('stop', self.__stop))
    self.cache: List[Message] = []


  def __get_chats(self) -> None:
    with open('chats.json', 'r') as f:
      self.chats = json.load(f)
      f.close()

  def __persist_chats(self) -> None:
      with open('chats.json', 'w') as f:
        json.dump(self.chats, f)
        f.close()


  def __add_chat(self, chat_id: int) -> None:
    if chat_id not in self.chats:
      logging.info('adding new chat')
      self.chats.append(chat_id)
      self.__persist_chats()

  def __remove_chat(self, chat_id: int) -> None:
    logging.info('removing the chat ' + str(chat_id))
    self.chats = [chat for chat in self.chats if chat != chat_id]
    self.__persist_chats()
    

  def __start(self, update: Update, context: CallbackContext) -> None:
    self.__add_chat(update.message.chat_id)
    logging.info(f'got new user with id {update.message.chat_id}')
    update.message.reply_text('Welcome to BurgerBot. When there will be slot - you will receive notification. To stop it - just type /stop')


  def __stop(self, update: Update, context: CallbackContext) -> None:
    self.__remove_chat(update.message.chat_id)
    update.message.reply_text('Thanks for using me! Bye!')

  def __parse(self) -> None:
    while True:
      page = requests.get(url)
      if page.status_code == 429:
        logging.info('exceeded rate limit. Sleeping for a while')
        time.sleep(300)
        next
      soup = BeautifulSoup(page.content, 'html.parser')

      c = soup.find('td', class_='buchbar')

      if c:
        logging.info('got appointment, notifing users')
        try:
          self.__send_message(c.a['href'])
        except Exception as e:
          logging.warn(e)
      else:
        logging.info("no luck yet")
      self.__clear_cache()
      time.sleep(30)


  def __poll(self) -> None:
    self.updater.start_polling()

  def __send_message(self, msg: str) -> None:
    if self.__msg_in_cache(msg):
      logging.info('Notification is cached already. Do not repeat sending')
      return
    self.__add_msg_to_cache(msg)
    md_msg = f"There are slots on {self.__date_from_msg(msg)} available for booking, click [here]({url}) to check it out"
    for c in self.chats:
      self.updater.bot.send_message(chat_id=c, text=md_msg, parse_mode=ParseMode.MARKDOWN_V2)

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
      logging.info('clearing some messages from cache')
      self.cache = [m for m in self.cache if (cur_ts - m.ts) < 300]

  def __date_from_msg(self, msg: str) -> str:
    msg_arr = msg.split('/')
    ts = msg_arr[len(msg_arr) - 2] + 7200 # adding two hours to match Berlin TZ with UTC
    return datetime.fromtimestamp(int(ts)).strftime("%d %B")


  def start(self) -> None:
    logging.info('starting bot')
    parse_task = threading.Thread(target=self.__parse)
    poll_task = threading.Thread(target=self.__poll)
    parse_task.start()
    poll_task.start()
    parse_task.join()
    poll_task.join()
  

def main() -> None:
  bot = Bot()
  bot.start()

if __name__ == '__main__':
  log_level = os.getenv('LOG_LEVEL', 'INFO')
  logging.basicConfig(
    level=log_level, 
    format="%(asctime)s [%(levelname)-5.5s] %(message)s", 
    handlers=[logging.StreamHandler(sys.stdout)],)
  main()