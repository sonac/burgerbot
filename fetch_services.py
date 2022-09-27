#!/usr/bin/env python3

import logging
import sys
import time
from parser import ServiceParser
from typing import List

from config import Config
from fetcher import Fetcher
from services import Service, supported_services

fetcher = Fetcher(bot_email=Config.bot_email, bot_id=Config.bot_id)
parser = ServiceParser(fetcher=fetcher)


def main() -> None:
    services: List[Service] = []

    for service_id in supported_services:
        try:
            service = parser.parse(service_id=service_id)
            services.append(service)
            time.sleep(2)
        except Exception as e:
            logging.warning("could not fetch service %d: %s", service_id, e)

    print(services)


if __name__ == "__main__":
    log_level = Config.log_level
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)-5.5s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    main()
