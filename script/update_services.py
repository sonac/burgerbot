#!/usr/bin/env python3

import logging
import sys
from typing import List

from burgerbot.config import Config
from burgerbot.parser import ServiceParser
from burgerbot.services import Service, ServicesManager, supported_services
from tests.FixtureFetcher import FixtureFetcher

fixture_fetcher = FixtureFetcher()
parser = ServiceParser(fetcher=fixture_fetcher)
manager = ServicesManager(filename=Config.services_file)


def main() -> None:
    services: List[Service] = []

    for service_id in supported_services:
        try:
            service = parser.parse(service_id=service_id)
            services.append(service)
        except Exception as e:
            logging.warning("could not fetch service %d: %s", service_id, e)

    manager.save(services=services)

    print(f"...done, written to {manager.filename}")


if __name__ == "__main__":
    log_level = Config.log_level
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)-5.5s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    main()
