import logging
import urllib.parse
from datetime import datetime
from email.mime import base
from time import mktime
from typing import List, Optional

import bs4
import pytz
from dateutil import relativedelta

from burgerbot.fetcher import Fetcher
from burgerbot.model import SlotResult


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

    def __parse_page(self, content: bytes, base_url: str) -> List[SlotResult]:
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
                url = url_for_slot(base_url, slot)  # load via request.url
                if date is None or url is None:
                    logging.warning("could not parse slot")
                    continue

                results.append(SlotResult(date, url))

            return results

        except Exception as e:  ## sometimes shit happens
            logging.warning(e)

        return []

    def parse(self, url: str) -> List[SlotResult]:
        session = self.fetcher.start_session()

        content_page_1 = self.fetcher.fetch(url, session=session)
        results_page_1 = self.__parse_page(content_page_1, base_url=url)

        # I'm sureeee around midnight at the change of the month this is wrong, but eh.
        today = datetime.now(pytz.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        in_two_months = today + relativedelta.relativedelta(months=2, day=1)
        in_two_months_timestamp = int(mktime(in_two_months.timetuple()))
        page_2_url = f"https://service.berlin.de/terminvereinbarung/termin/day/{in_two_months_timestamp}/"

        content_page_2 = self.fetcher.fetch(page_2_url, session=session)
        results_page_2 = self.__parse_page(content_page_2, base_url=page_2_url)

        if session is not None:
            session.close()

        return results_page_1 + results_page_2
