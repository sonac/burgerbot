#!/usr/bin/env python3

import logging
import sys
import time

from burgerbot.config import Config
from burgerbot.fetcher import LiveFetcher
from burgerbot.services import supported_services
from burgerbot.urls import service_url_template

fetcher = LiveFetcher(bot_email=Config.bot_email, bot_id=Config.bot_id)


def main() -> None:
    for service_id in supported_services:
        try:
            print(f"Fetching service {service_id}")

            url = service_url_template.format(id=service_id)
            path = f"tests/fixtures/service/{service_id}.html"

            content = fetcher.fetch(url)

            file = open(path, "wb")
            file.write(content)
            file.close()

            print("...done")

        except Exception as e:
            logging.warning("could not fetch service %d: %s", service_id, e)

        time.sleep(1)


if __name__ == "__main__":
    log_level = Config.log_level
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)-5.5s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    main()
