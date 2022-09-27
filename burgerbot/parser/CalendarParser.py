import logging
import urllib.parse
from datetime import datetime
from typing import List, Optional

import bs4
import pytz
import requests

from burgerbot.fetcher import Fetcher
from burgerbot.model import SlotResult


def date_title_for_slot(slot: bs4.element.Tag):
    table = slot.find_parent("table")

    if table is None:
        return None

    title = table.find("th", class_="month")

    if title is None:
        return None

    return title.text


def date_for_slot(slot: bs4.element.Tag):
    link = slot.a

    if link is None:
        return None

    href = link.get("href")

    if href is None:
        return None

    if isinstance(href, list):
        href = href[0]

    # href hopefully looks like:
    # https://service.berlin.de/terminvereinbarung/termin/time/1669071600/

    parts: List[str] = href.split("/")

    timestamp = int(parts[-2])
    utc_date = datetime.fromtimestamp(timestamp, pytz.utc)
    berlin_date = utc_date.astimezone(pytz.timezone("Europe/Berlin"))

    return berlin_date


def url_for_slot(base_url: str, slot: bs4.element.Tag) -> Optional[str]:
    link = slot.a
    if link is None:
        return None

    href = link.get("href")

    if href is None:
        return None

    if isinstance(href, list):
        href = href[0]

    return urllib.parse.urljoin(base_url, href)


class CalendarParser:
    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    def __parse_page(self, content: bytes) -> List[SlotResult]:
        try:
            soup = bs4.BeautifulSoup(content, "html.parser")

            available_slots: List[bs4.element.Tag] = soup.find_all(
                "td", class_="buchbar"
            )
            unavailable_slots: List[bs4.element.Tag] = soup.find_all(
                "td", class_="nichtbuchbar"
            )

            is_valid = len(available_slots) > 0 or len(unavailable_slots) > 0
            if is_valid:
                logging.info("page is valid")
            else:
                logging.warn("looks like we've been soft-rate-limited")
                return []

            if len(available_slots) == 0:
                logging.info("no luck yet")

            results: List[SlotResult] = []
            for slot in available_slots:
                date = date_for_slot(slot)
                url = url_for_slot("", slot)  # load via request.url
                if date is None or url is None:
                    logging.warning("could not parse slot")
                    continue

                results.append(SlotResult(date, url))

            return results

        except Exception as e:  ## sometimes shit happens
            logging.warning(e)

        return []

    def parse(self, url: str) -> List[SlotResult]:
        content = self.fetcher.fetch(url)
        return self.__parse_page(content)
