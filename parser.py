import time
import logging
from dataclasses import dataclass
from typing import List
from re import S

import requests
from bs4 import BeautifulSoup

default_url = "https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=0&anliegen[]={}&dienstleisterlist=122210,122217,327316,122219,327312,122227,327314,122231,327346,122243,327348,122252,329742,122260,329745,122262,329748,122254,329751,122271,327278,122273,327274,122277,327276,330436,122280,327294,122282,327290,122284,327292,327539,122291,327270,122285,327266,122286,327264,122296,327268,150230,329760,122301,327282,122297,327286,122294,327284,122312,329763,122314,329775,122304,327330,122311,327334,122309,327332,122281,327352,122279,329772,122276,327324,122274,327326,122267,329766,122246,327318,122251,327320,122257,327322,122208,327298,122226,327300,121362,121364&herkunft=http%3A%2F%2Fservice.berlin.de%2Fdienstleistung%2F120686%2F"

naturalization_url = "https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=1&dienstleister=324261&anliegen[]=318998&herkunft=1"


def build_url(id: int) -> str:
    if id == 318998:
        return naturalization_url.format(id)
    return default_url.format(id)


@dataclass
class Slot:
    msg: str
    service_id: int


class Parser:
    def __init__(self, services: List[int]) -> None:
        self.services = services
        self.proxy_on: bool = False
        self.parse()

    def __get_url(self, url) -> requests.Response:
        logging.debug(url)
        try:
            if self.proxy_on:
                return requests.get(url, proxies={"https": "socks5://127.0.0.1:9050"})
            return requests.get(url)
        except Exception as err:
            logging.warn(
                "received an error from the server, waiting for 1 minute before retry"
            )
            logging.warn(err)
            time.sleep(60)
            return self.__get_url(url)

    def __toggle_proxy(self) -> None:
        self.proxy_on = not self.proxy_on

    def __parse_page(self, page, service_id) -> List[str]:
        try:
            if page.status_code == 428 or page.status_code == 429:
                logging.info("exceeded rate limit. Sleeping for a while")
                time.sleep(299)
                self.__toggle_proxy()
                return []
            soup = BeautifulSoup(page.content, "html.parser")
            slots = soup.find_all("td", class_="buchbar")
            is_valid = soup.find_all("td", class_="nichtbuchbar")
            if len(is_valid) > 0:
                logging.info("page is valid")
            else:
                logging.debug(page)
            if len(slots) == 0:
                logging.info("no luck yet")
            return [Slot(slot.a["href"], service_id) for slot in slots]
        except Exception as e:  ## sometimes shit happens
            logging.error(f"error occured during page parsing, {e}")
            self.__toggle_proxy()

    def add_service(self, service_id: int) -> None:
        self.services.append(service_id)

    def parse(self) -> List[str]:
        slots = []
        logging.info("services are: " + str(self.services))
        for svc in self.services:
            page = self.__get_url(build_url(svc))
            slots += self.__parse_page(page, svc)
        return slots
