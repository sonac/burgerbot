## BurgerBot

I was frustrated with the lack of available slots in Burgeramt, so I've created this bot for myself, to catch one that available. It's pretty straightforward, once per 30 seconds it parses page with all appointments in all Berlin Burgeramts and if there is available slot for current and next month - it notifies in telegram with the link to registration.

## Set up

### Install `poetry`

Instructions via: https://python-poetry.org/docs/#installing-manually

```
python3 -m venv venv
pip install -U pip setuptools
pip install poetry
pre-commit install
```

### Initialise Development Environment

```
source venv/bin/activate
poetry install
```
