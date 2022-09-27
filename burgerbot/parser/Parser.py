import logging
from typing import List

from burgerbot.fetcher import Fetcher
from burgerbot.model import Slot
from burgerbot.parser.CalendarParser import CalendarParser
from burgerbot.parser.ServiceParser import ServiceParser
from burgerbot.services import Service
from burgerbot.urls import build_default_url


class Parser:
    def __init__(self, fetcher: Fetcher, services: List[Service]) -> None:
        self.fetcher = fetcher
        self.all_services = services

        self.calendar_parser = CalendarParser(self.fetcher)

    def __url_for_service(self, service: Service) -> str:

        if service.city_wide_url is not None:
            return service.city_wide_url

        if len(service.location_urls) == 0:
            raise Exception(f"service {service.id} has no locations")

        # TODO: this helps The Author™ find an appointment!
        if service.id == 318998:
            # find the location with "326509", aka Bezirksamt Treptow-Köpenick
            return next((lu for lu in service.location_urls.values() if "326509" in lu))

        # TODO: figure out how to specify a location
        return next(iter(service.location_urls.values()))

    def parse(self, services: List[int]) -> List[Slot]:
        logging.info("services to check: " + str(services))

        slots: List[Slot] = []
        for service_id in services:
            service = next((s for s in self.all_services if s.id == service_id), None)

            if service is None:
                raise Exception(f"could not find service for id {service_id}")

            url = self.__url_for_service(service)

            logging.debug(f"URL for service {service_id}: {url}")

            results = self.calendar_parser.parse(url)

            slots += [Slot(service=service, result=result) for result in results]
        return slots
