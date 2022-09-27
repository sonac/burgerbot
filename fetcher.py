import logging
import time
from typing import Optional

import requests


class RateLimitedException(Exception):
    pass


class Fetcher:
    proxy: Optional[str]

    def __init__(self, bot_email: str, bot_id: str) -> None:
        # self.proxy = "socks5://127.0.0.1:9050"

        self.bot_email = bot_email
        self.bot_id = bot_id

    def fetch(self, url: str) -> requests.Response:
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

            response = requests.get(url, headers=headers, proxies=proxies)

            if response.status_code in [428, 429]:
                raise RateLimitedException(response)

            return response
        except Exception as err:
            logging.warning(
                "received an error from the server: %s",
                err,
            )

            raise err
