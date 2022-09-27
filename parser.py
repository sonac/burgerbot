import logging
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from re import S
from typing import List, Optional

import bs4
import pytz
import requests

from fetcher import Fetcher
from services import Service

service_url_template = "https://service.berlin.de/dienstleistung/{id}/"

# we will try to detect URLs where possible and cache them, but these can be used as a fallback
default_dienstleisterlist = "122210,122217,327316,122219,327312,122227,327314,122231,327346,122243,327348,122252,329742,122260,329745,122262,329748,122254,329751,122271,327278,122273,327274,122277,327276,330436,122280,327294,122282,327290,122284,327292,327539,122291,327270,122285,327266,122286,327264,122296,327268,150230,329760,122301,327282,122297,327286,122294,327284,122312,329763,122314,329775,122304,327330,122311,327334,122309,327332,122281,327352,122279,329772,122276,327324,122274,327326,122267,329766,122246,327318,122251,327320,122257,327322,122208,327298,122226,327300,121362,121364"
default_url_template = "https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=0&anliegen[]={id}&dienstleisterlist={dienstleisterlist}&herkunft=http%3A%2F%2Fservice.berlin.de%2Fdienstleistung%2F120686%2F"

naturalization_dienstleister = (
    "326509"  # hardcoded default: Bezirksamt Treptow-Köpenick
)
naturalization_url_template = "https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=1&dienstleister={dienstleister}&anliegen[]={id}&herkunft=1"


def build_default_url(service_id: int) -> str:
    if service_id == 318998:
        return naturalization_url_template.format(
            id=service_id, dienstleister=naturalization_dienstleister
        )
    return default_url_template.format(
        id=service_id, dienstleisterlist=default_dienstleisterlist
    )


@dataclass
class SlotResult:
    date: datetime
    url: str


@dataclass
class Slot:
    service: Service
    result: SlotResult


class ServiceParser:
    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    def __parse_page(self, response: requests.Response) -> Optional[str]:
        try:
            soup = bs4.BeautifulSoup(response.content, "html.parser")
            link = soup.find("a", text="Termin berlinweit suchen")

            if link is None:
                return None

            if isinstance(link, bs4.element.NavigableString):
                return None

            href = link.get("href")

            if href is None:
                return None

            if isinstance(href, list):
                href = href[0]

            return href

        except Exception as e:  ## sometimes shit happens
            logging.warning(e)

        return None

    def parse(self, service_id: int) -> Service:
        request_url = service_url_template.format(id=service_id)
        response = self.fetcher.fetch(request_url)

        response.raise_for_status

        service_url = self.__parse_page(response)

        if service_url is None:
            raise Exception(f"Could not parse service at URL: {request_url}")

        return Service(id=service_id, name="todo: name", city_wide_url=service_url)


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

    def __parse_page(self, response: requests.Response) -> List[SlotResult]:
        try:
            soup = bs4.BeautifulSoup(response.content, "html.parser")

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
                url = url_for_slot(response.url, slot)
                if date is None or url is None:
                    logging.warning("could not parse slot")
                    continue

                results.append(SlotResult(date, url))

            return results

        except Exception as e:  ## sometimes shit happens
            logging.warning(e)

        return []

    def parse(self, url: str) -> List[SlotResult]:
        response = self.fetcher.fetch(url)

        if not response.ok:
            return []

        return self.__parse_page(response)


class Parser:
    cached_services: dict[int, Service] = {}
    unavailable_services: set[int] = set()

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

        self.calendar_parser = CalendarParser(self.fetcher)
        self.service_parser = ServiceParser(self.fetcher)

    def __url_for_service(self, service_id: int) -> str:
        # don't try to look up services that are known to fail
        if service_id in self.unavailable_services:
            return build_default_url(service_id)

        if service_id not in self.cached_services:
            # try to detect the URL from the service page
            try:
                service = self.service_parser.parse(service_id)
                self.cached_services[service_id] = service
            except:
                self.unavailable_services.add(service_id)
                return build_default_url(service_id)

        return self.cached_services[service_id].city_wide_url

    def parse(self, services: List[int]) -> List[Slot]:
        logging.info("services are: " + str(services))

        slots: List[Slot] = []
        for service_id in services:
            url = self.__url_for_service(service_id)

            results = self.calendar_parser.parse(url)

            service = Service(id=service_id, name="todo: name", city_wide_url=url)
            slots += [Slot(service=service, result=result) for result in results]
        return slots
