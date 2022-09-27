## BurgerBot

I was frustrated with the lack of available slots in Burgeramt, so I've created this bot for myself, to catch one that available. It's pretty straightforward, once per 30 seconds it parses page with all appointments in all Berlin Burgeramts and if there is available slot for current and next month - it notifies in telegram with the link to registration.

## Set up

### Install `poetry`

Instructions via: https://python-poetry.org/docs/#installing-manually

```
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools
pip install poetry
poetry install
pre-commit install
```

### Initialise Development Environment

```
source .venv/bin/activate
poetry install
```

### Environment Variables

`TELEGRAM_API_KEY` (required): API key for your Telegram bot. More information [here](https://core.telegram.org/bots).
`LOG_LEVEL` (optional): Set logging level. Available options [here](https://docs.python.org/3/library/logging.html#levels).

### Proxy

Sometimes we get rate limited, so we can use a proxy to try and dodge it. Setting up a proxy on `127.0.0.1:9050` will do the job.

## Running

```
python3 ./burgerbot.py
```
