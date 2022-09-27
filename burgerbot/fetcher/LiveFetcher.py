import logging
import time
from typing import Optional

import requests

from burgerbot.fetcher.Fetcher import Fetcher
from burgerbot.fetcher.RateLimitedException import RateLimitedException


class LiveFetcher(Fetcher):
    proxy: Optional[str]

    def __init__(self, bot_email: str, bot_id: str) -> None:
        # self.proxy = "socks5://127.0.0.1:9050"
        self.proxy = None

        self.bot_email = bot_email
        self.bot_id = bot_id

    def fetch(self, url: str) -> bytes:
        logging.debug(f"Fetching {url}")

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": f"Mozilla/5.0 BurgerBot/1.1 (https://github.com/sonac/burgerbot; {self.bot_email}; {self.bot_id})",
            "Accept-Language": "en-gb",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        try:
            if self.proxy is not None:
                proxies = {"http": self.proxy, "https": self.proxy}
            else:
                proxies = None

            response = requests.get(url, headers=headers, proxies=proxies)

            if response.status_code in [428, 429]:
                raise RateLimitedException(response)

            response.raise_for_status()

            return response.content
        except Exception as err:
            logging.warning(
                "received an error from the server: %s",
                err,
            )

            raise err
