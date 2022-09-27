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

    def parse(self, services: List[int]) -> List[Slot]:
        logging.info("services to check: " + str(services))

        slots: List[Slot] = []
        for service_id in services:
            service = next((s for s in self.all_services if s.id == service_id), None)

            if service is None:
                raise Exception(f"could not find service for id {service_id}")

            url = service.best_url

            logging.debug(f"URL for service {service_id}: {url}")

            results = self.calendar_parser.parse(url)

            slots += [Slot(service=service, result=result) for result in results]
        return slots
