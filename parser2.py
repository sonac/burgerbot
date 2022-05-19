import time
import logging
from dataclasses import dataclass
from typing import List 
from re import S

import requests
from bs4 import BeautifulSoup

@dataclass
class Alert:
  msg: str

class Parser2:
  def __init__(self, personal_link: str) -> None:
    self.personal_link = personal_link
    self.proxy_on: bool = False
    self.parse()

  def __get_url(self, url) -> requests.Response:
    if self.proxy_on:
      return requests.get(url, proxies={'https': 'socks5://127.0.0.1:9050'})
    return requests.get(url)

  def __toggle_proxy(self) -> None:
    self.proxy_on = not self.proxy_on

  def __parse_page(self, page) -> List[str]:
    try:
      if page.status_code == 428:
        logging.info('exceeded rate limit. Sleeping for a while')
        time.sleep(299)
        self.__toggle_proxy()
        return None
      soup = BeautifulSoup(page.content, 'html.parser2')
      errors = soup.find_all('li', class_='errorMessage')
      if len(errors) != 0:
        logging.info("no luck yet")
      return [Alert('no error')]
    except Exception as e: ## sometimes shit happens
      logging.warn(e)
      self.__toggle_proxy()

  def set_personal_link(self, personal_link: str) -> None:
    self.personal_link

  def parse(self) -> List[str]:
    alerts = []
    page = self.__get_url(self.personal_link)
    alerts += self.__parse_page(page)
    return alerts
