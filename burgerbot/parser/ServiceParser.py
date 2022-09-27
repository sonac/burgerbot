import logging
from typing import Dict, List, Optional

import bs4

from burgerbot.fetcher import Fetcher
from burgerbot.services import Service
from burgerbot.urls import service_url_template


class ServiceParser:
    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    def __find_title(self, soup: bs4.BeautifulSoup) -> str:
        title = soup.find("h1", class_="title")

        if title is None:
            raise Exception("could not find title")

        return title.text

    def __find_service_url(self, soup: bs4.BeautifulSoup) -> Optional[str]:
        link = soup.find("a", text="Termin berlinweit suchen")

        if link is None:
            return None

        if isinstance(link, bs4.element.NavigableString):
            raise Exception("unexepected type for link (got NavigableString)")

        href = link.get("href")

        if href is None:
            raise Exception("could not find href")

        if isinstance(href, list):
            href = href[0]

        return href

    def __find_location_urls(self, soup: bs4.BeautifulSoup) -> Dict[str, str]:
        azlist = soup.find("div", class_="azlist")

        results: Dict[str, str] = {}

        if azlist is None:
            return results

        if isinstance(azlist, bs4.element.NavigableString):
            raise Exception("unexepected type for azlist (got NavigableString)")

        locations: List[bs4.element.Tag] = azlist.find_all(
            "div", class_="behoerdenitem"
        )

        for location in locations:
            location_title: Optional[str] = None

            location_title_h4 = location.find("h4")
            if location_title_h4 is not None and isinstance(
                location_title_h4, bs4.element.Tag
            ):
                location_title = location_title_h4.text

            rows: List[bs4.element.Tag] = location.find_all("div", class_="row")

            for row in rows:
                link = row.find("a", class_="termin-buchen")

                if link is None:
                    continue

                if isinstance(link, bs4.element.NavigableString):
                    raise Exception("unexepected type for link (got NavigableString)")

                href = link.get("href")

                if href is None:
                    raise Exception("could not find href")

                if isinstance(href, list):
                    href = href[0]

                # title can be a "header" (i.e. entire bezirk) or a "link" (i.e. a specific location)
                location_h = row.find("h4")
                location_p = row.find("a", class_="referdienstleister")

                if location_h is not None:
                    results[location_h.text] = href
                elif location_p is not None:
                    # prepend bezirk title to the location
                    if location_title is not None:
                        title = f"{location_title}: {location_p.text}"
                    else:
                        title = location_p.text

                    results[title] = href

        return results

    def parse(self, service_id: int) -> Service:
        request_url = service_url_template.format(id=service_id)
        content = self.fetcher.fetch(request_url)

        soup = bs4.BeautifulSoup(content, "html.parser")

        return Service(
            id=service_id,
            title=self.__find_title(soup),
            city_wide_url=self.__find_service_url(soup),
            location_urls=self.__find_location_urls(soup),
        )
