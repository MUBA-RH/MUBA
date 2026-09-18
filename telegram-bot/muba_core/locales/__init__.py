"""Complete, validated response catalogs for every supported language."""
from .ar import CATALOG as AR
from .en import CATALOG as EN
from .hi import CATALOG as HI
from .tr import CATALOG as TR
from .zh import CATALOG as ZH

CATALOGS={"en":EN,"tr":TR,"zh":ZH,"ar":AR,"hi":HI}
SUPPORTED_LANGUAGES=tuple(CATALOGS)
REQUIRED_KEYS=frozenset(EN)

def validate_catalogs():
    for language,catalog in CATALOGS.items():
        missing=REQUIRED_KEYS-set(catalog); extra=set(catalog)-REQUIRED_KEYS
        if missing or extra:
            raise RuntimeError(f"Invalid {language} response catalog; missing={sorted(missing)}, extra={sorted(extra)}")
        if any(not value for value in catalog.values()):
            raise RuntimeError(f"Empty response in {language} catalog")

def text(language,key):
    return CATALOGS.get(language,EN)[key]

def choices(language,key):
    value=CATALOGS.get(language,EN)[key]
    if not isinstance(value,tuple): raise TypeError(f"Response key {key!r} is not a choice tuple")
    return value

validate_catalogs()
