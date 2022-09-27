from burgerbot.fetcher import Fetcher


class FixtureFetcher(Fetcher):
    def fetch(self, url: str) -> bytes:
        id = url.split("/")[-2]

        file = open(f"tests/fixtures/service/{id}.html", "rb")
        contents = file.read()
        file.close()

        return contents
