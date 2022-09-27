from dataclasses import dataclass
from datetime import datetime

from burgerbot.services import Service


@dataclass
class SlotResult:
    date: datetime
    url: str


@dataclass
class Slot:
    service: Service
    result: SlotResult
