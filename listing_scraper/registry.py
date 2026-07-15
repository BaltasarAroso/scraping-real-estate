from listing_scraper.parsers.base import Provider
from listing_scraper.parsers.idealista import IdealistaProvider
from listing_scraper.parsers.imovirtual import ImovirtualProvider
from listing_scraper.parsers.jsonld import JsonLdProvider
from listing_scraper.parsers.properstar import ProperstarProvider

PROVIDERS: list[Provider] = [
    ProperstarProvider(),
    IdealistaProvider(),
    ImovirtualProvider(),
    JsonLdProvider(),
]


def provider_for_url(url: str) -> Provider | None:
    for provider in PROVIDERS:
        if provider.matches(url):
            return provider
    return None
