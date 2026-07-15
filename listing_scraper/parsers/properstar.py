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

LISTING_RE = re.compile(r"/anuncio/(\d+)", re.I)


class ProperstarProvider(Provider):
    name = "properstar"

    def matches(self, url: str) -> bool:
        host = url.lower()
        return "properstar.pt" in host and bool(LISTING_RE.search(url))

    def listing_id(self, url: str) -> str:
        match = LISTING_RE.search(url)
        if not match:
            raise ValueError("Invalid Properstar listing URL")
        return match.group(1)

    def playwright_ready_expression(self) -> str | None:
        return (
            "() => [...document.querySelectorAll('script[type=\"application/ld+json\"]')]"
            ".some((node) => node.textContent.includes('RealEstateListing'))"
        )

    def parse(self, url: str, html: str, *, source: str) -> ListingData:
        listing = find_json_ld(html, "RealEstateListing")
        if not listing:
            raise ValueError("Properstar listing data not found")

        address = listing.get("mainEntity", {}).get("address", {})
        offers = listing.get("offers", {})

        return ListingData(
            url=url,
            provider=self.name,
            listing_id=self.listing_id(url),
            distrito=normalize_distrito(address.get("addressRegion")),
            concelho=address.get("addressLocality"),
            tipologia=parse_tipologia(
                listing.get("name", ""),
                html,
                bedrooms=listing.get("mainEntity", {}).get("numberOfBedrooms"),
            ),
            area_bruta_privativa_m2=parse_area_from_html(html),
            preco_eur=offers.get("price"),
            source=source,
        )
