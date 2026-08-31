from pathlib import Path

from fluent.runtime import FluentLocalization, FluentResourceLoader

LOCALES_DIR = Path(__file__).parent / "locales"
DEFAULT_LANGUAGE = "en"


def get_localization(locale: str = DEFAULT_LANGUAGE) -> FluentLocalization:
    loader = FluentResourceLoader(str(LOCALES_DIR / "{locale}"))
    return FluentLocalization([locale], ["main.ftl"], loader)
