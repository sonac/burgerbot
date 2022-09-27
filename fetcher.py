import logging
import time

import requests


class Fetcher:
    proxy_available = False

    def __init__(self, bot_email: str, bot_id: str) -> None:
        self.proxy_on: bool = False

        self.bot_email = bot_email
        self.bot_id = bot_id

    def toggle_proxy(self) -> None:
        self.proxy_on = self.proxy_available and not self.proxy_on

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
            if self.proxy_on:
                response = requests.get(
                    url, proxies={"https": "socks5://127.0.0.1:9050"}, headers=headers
                )
            else:
                response = requests.get(url, headers=headers)

            if response.status_code in [428, 429]:
                logging.info("exceeded rate limit. Sleeping for a while")
                self.toggle_proxy()
                time.sleep(300)

            return response
        except Exception as err:
            logging.warning(
                "received an error from the server, waiting for 1 minute before retry: %s",
                err,
            )
            time.sleep(60)
            return self.fetch(url)
