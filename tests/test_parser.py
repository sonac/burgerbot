from ward import each, fixture, raises, test

from burgerbot.parser import ServiceParser
from burgerbot.services import supported_services
from tests.FixtureFetcher import FixtureFetcher


@test("parse() returns a Service with city-wide URL")
def _():
    mock_fetcher = FixtureFetcher()
    parser = ServiceParser(fetcher=mock_fetcher)
    service = parser.parse(service_id=327537)

    assert service.id == 327537
    assert (
        service.title
        == "Fahrerlaubnis - Umschreibung einer ausländischen Fahrerlaubnis aus einem Nicht-EU/EWR-Land (Drittstaat/Anlage 11)"
    )
    assert (
        service.city_wide_url
        == "https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=1&anliegen[]=327537&dienstleisterlist=122210,122217,122219,122227,122231,122243,122252,122260,122262,122254,122271,122273,122277,122280,122282,122284,327539,122291,122285,122286,122296,150230,122301,122297,122294,122312,122314,122304,122311,122309,317869,122281,122279,122276,122274,122267,122246,122251,122257,122208,122226&herkunft=http%3A%2F%2Fservice.berlin.de%2Fdienstleistung%2F327537%2F"
    )


@test("parse() returns a Service without city-wide URL")
def _():
    mock_fetcher = FixtureFetcher()
    parser = ServiceParser(fetcher=mock_fetcher)
    service = parser.parse(service_id=318998)

    assert service.id == 318998
    assert (
        service.title
        == "Einbürgerung - Verleihung der deutschen Staatsangehörigkeit beantragen"
    )
    assert service.city_wide_url is None
    assert "Bezirksamt Charlottenburg - Wilmersdorf" not in service.location_urls
    assert (
        service.location_urls[
            "Bezirksamt Marzahn - Hellersdorf: Einb\u00fcrgerung/Staatsangeh\u00f6rigkeitsangelegenheiten Marzahn-Hellersdorf"
        ]
        == "https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=1&dienstleister=324261&anliegen[]=318998&herkunft=1"
    )


for service_id in supported_services:

    @test("parses service fixture: {service_id}.html")
    def _(service_id=service_id):
        mock_fetcher = FixtureFetcher()
        parser = ServiceParser(fetcher=mock_fetcher)
        service = parser.parse(service_id=service_id)

        assert service.id == service_id
