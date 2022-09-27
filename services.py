from dataclasses import dataclass

supported_services = [
    120335,  # Abmeldung einer Wohnung
    120686,  # Anmeldung
    120701,  # Personalausweis beantragen
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
class Service:
    id: int
    name: str
    city_wide_url: str
