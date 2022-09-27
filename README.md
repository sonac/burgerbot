## BurgerBot

From the original README:

> I was frustrated with the lack of available slots in Burgeramt, so I've created this bot for myself, to catch one that available. It's pretty straightforward, once per 30 seconds it parses page with all appointments in all Berlin Burgeramts and if there is available slot for current and next month - it notifies in telegram with the link to registration.

## Set up

### Install `poetry`

Instructions via: https://python-poetry.org/docs/#installing-manually

```
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools
pip install poetry
```

### Initialise Development Environment

```
source .venv/bin/activate
poetry install
pre-commit install
```

### Environment Variables

- `TELEGRAM_API_KEY` (required): API key for your Telegram bot. More information [here](https://core.telegram.org/bots).
- `BOT_EMAIL` (required): Email addressed used in request headers to identify bot.
- `BOT_ID` (required): Unique string used in request headers to identify bot.
- `LOG_LEVEL` (optional): Set logging level. Available options [here](https://docs.python.org/3/library/logging.html#levels).

## Running

```
python3 ./burgerbot/bot.py
```

## Acknowledgements

- [sonac/burgerbot](https://github.com/sonac/burgerbot) was the original code this was based off
- [nicbou/burgeramt-appointments-websockets](https://github.com/nicbou/burgeramt-appointments-websockets) did a lot of the groundwork to determine the base standards - user agent, refresh interval, etc
