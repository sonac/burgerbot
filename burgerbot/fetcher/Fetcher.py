from typing import Optional

import requests


class Fetcher:
    def fetch(self, url: str, session: Optional[requests.Session] = None) -> bytes:
        ...

    def start_session(self) -> Optional[requests.Session]:
        ...
