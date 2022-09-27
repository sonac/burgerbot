import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from dataclasses_json import DataClassJsonMixin

supported_services = [
    120335,  # Abmeldung einer Wohnung
    120686,  # Anmeldung
    120702,  # Meldebescheinigung beantragen
    120703,  # Reisepass beantragen
    120914,  # Zulassung eines Fahrzeuges mit auswärtigem Kennzeichen mit Halterwechsel
    121469,  # Kinderreisepass beantragen / verlängern / aktualisieren
    121598,  # Fahrerlaubnis - Umschreibung einer ausländischen Fahrerlaubnis aus einem EU-/EWR-Staat
    121627,  # Fahrerlaubnis - Ersterteilung beantragen
    121701,  # Beglaubigung von Kopien
    121921,  # Gewerbeanmeldung
    318998,  # Einbürgerung - Verleihung der deutschen Staatsangehörigkeit beantragen
    324280,  # Niederlassungserlaubnis oder Erlaubnis
    326798,  # Blaue Karte EU auf einen neuen Pass übertragen
    327537,  # Fahrerlaubnis - Umschreibung einer ausländischen
]


@dataclass
class Service(DataClassJsonMixin):
    id: int
    title: str
    city_wide_url: Optional[str]
    location_urls: Dict[str, str]


class ServicesManager:
    _services: Optional[List[Service]] = None

    def __init__(self, filename: str) -> None:
        self.filename = filename

    @property
    def services(self) -> List[Service]:
        if self._services is None:
            self._services = self.load()

        return self._services

    def load(self) -> List[Service]:
        with open(self.filename, "r") as file:
            result = Service.schema().loads(file.read(), many=True)
            file.close()

            return result

    def save(self, services: List[Service]) -> None:
        self._services = None

        with open(self.filename, "w") as file:
            output = Service.schema().dumps(services, many=True)
            json.dump(output, file, indent=4)
            file.close()

    # convenience methods
    def get(self, id: int) -> Service:
        return next((s for s in self.services if s.id == id))

    @property
    def service_ids(self) -> List[int]:
        return [s.id for s in self.services]
