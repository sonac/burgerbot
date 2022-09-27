service_url_template = "https://service.berlin.de/dienstleistung/{id}/"

# we will try to detect URLs where possible and cache them, but these can be used as a fallback
default_dienstleisterlist = "122210,122217,327316,122219,327312,122227,327314,122231,327346,122243,327348,122252,329742,122260,329745,122262,329748,122254,329751,122271,327278,122273,327274,122277,327276,330436,122280,327294,122282,327290,122284,327292,327539,122291,327270,122285,327266,122286,327264,122296,327268,150230,329760,122301,327282,122297,327286,122294,327284,122312,329763,122314,329775,122304,327330,122311,327334,122309,327332,122281,327352,122279,329772,122276,327324,122274,327326,122267,329766,122246,327318,122251,327320,122257,327322,122208,327298,122226,327300,121362,121364"
default_url_template = "https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=0&anliegen[]={id}&dienstleisterlist={dienstleisterlist}&herkunft=http%3A%2F%2Fservice.berlin.de%2Fdienstleistung%2F120686%2F"

naturalization_dienstleister = (
    "326509"  # hardcoded default: Bezirksamt Treptow-Köpenick
)
naturalization_url_template = "https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=1&dienstleister={dienstleister}&anliegen[]={id}&herkunft=1"


def build_default_url(service_id: int) -> str:
    if service_id == 318998:
        return naturalization_url_template.format(
            id=service_id, dienstleister=naturalization_dienstleister
        )
    return default_url_template.format(
        id=service_id, dienstleisterlist=default_dienstleisterlist
    )
