from typing import Optional

import requests

from burgerbot.fetcher import Fetcher


class FixtureFetcher(Fetcher):
    def start_session(self) -> Optional[requests.Session]:
        return None

    def fetch(self, url: str, session: Optional[requests.Session] = None) -> bytes:
        id = url.split("/")[-2]

        file = open(f"tests/fixtures/service/{id}.html", "rb")
        contents = file.read()
        file.close()

        return contents
