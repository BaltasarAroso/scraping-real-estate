from __future__ import annotations

import re

from listing_scraper.models import ListingData
from listing_scraper.parsers.base import Provider
from listing_scraper.parsers.common import (
    find_json_ld,
    normalize_distrito,
    parse_area_from_html,
    parse_tipologia,
)

LISTING_RE = re.compile(r"(\d{5,})", re.I)


class JsonLdProvider(Provider):
    name = "jsonld"

    def matches(self, url: str) -> bool:
        return bool(LISTING_RE.search(url))

    def listing_id(self, url: str) -> str:
        match = LISTING_RE.search(url)
        if not match:
            raise ValueError("Could not determine listing id from URL")
        return match.group(1)

    def playwright_ready_expression(self) -> str | None:
        return (
            "() => [...document.querySelectorAll('script[type=\"application/ld+json\"]')]"
            ".some((node) => /RealEstateListing|Product|Apartment|House/i.test(node.textContent))"
        )

    def parse(self, url: str, html: str, *, source: str) -> ListingData:
        listing = find_json_ld(
            html,
            "RealEstateListing",
            "Product",
            "Apartment",
            "House",
            "SingleFamilyResidence",
        )
        if not listing:
            raise ValueError("Generic JSON-LD listing data not found")

        entity = listing.get("mainEntity", listing)
        address = entity.get("address", listing.get("address", {}))
        offers = listing.get("offers", {})
        if isinstance(offers, list) and offers:
            offers = offers[0]

        return ListingData(
            url=url,
            provider=self.name,
            listing_id=self.listing_id(url),
            distrito=normalize_distrito(address.get("addressRegion")),
            concelho=address.get("addressLocality"),
            tipologia=parse_tipologia(
                listing.get("name", ""),
                html,
                bedrooms=entity.get("numberOfBedrooms"),
            ),
            area_bruta_privativa_m2=parse_area_from_html(html),
            preco_eur=offers.get("price") if isinstance(offers, dict) else None,
            source=source,
        )
