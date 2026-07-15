from __future__ import annotations

import re

from listing_scraper.models import ListingData
from listing_scraper.parsers.base import Provider
from listing_scraper.parsers.common import (
    normalize_distrito,
    parse_next_data,
    parse_price_number,
    parse_tipologia,
)

LISTING_RE = re.compile(r"-ID([\w-]+)$", re.I)


class ImovirtualProvider(Provider):
    name = "imovirtual"

    def matches(self, url: str) -> bool:
        lowered = url.lower()
        return "imovirtual.com" in lowered and "/pt/anuncio/" in lowered and "-id" in lowered

    def listing_id(self, url: str) -> str:
        match = LISTING_RE.search(url.rstrip("/"))
        if not match:
            raise ValueError("Invalid Imovirtual listing URL")
        return match.group(1)

    def playwright_ready_expression(self) -> str | None:
        return "() => !!document.querySelector('#__NEXT_DATA__')"

    def _location_levels(self, unified_ad: dict) -> dict[str, str]:
        levels: dict[str, str] = {}
        locations = (
            unified_ad.get("location", {})
            .get("reverseGeocoding", {})
            .get("locations", [])
        )
        for item in locations:
            if not isinstance(item, dict):
                continue
            level = item.get("locationLevel")
            name = item.get("name")
            if level and name:
                levels[str(level)] = str(name)
        return levels

    def parse(self, url: str, html: str, *, source: str) -> ListingData:
        next_data = parse_next_data(html)
        if not next_data:
            raise ValueError("Imovirtual listing data not found")

        unified_ad = next_data.get("props", {}).get("pageProps", {}).get("unifiedAd")
        if not isinstance(unified_ad, dict):
            raise ValueError("Imovirtual unifiedAd payload missing")

        levels = self._location_levels(unified_ad)
        attributes = unified_ad.get("attributes") or {}
        area = attributes.get("m") or attributes.get("area") or attributes.get("gross_area")

        return ListingData(
            url=url,
            provider=self.name,
            listing_id=self.listing_id(url),
            distrito=normalize_distrito(levels.get("district")),
            concelho=levels.get("council"),
            tipologia=parse_tipologia(unified_ad.get("title", ""), html),
            area_bruta_privativa_m2=str(area).replace(",", ".") if area else None,
            preco_eur=parse_price_number(unified_ad.get("price")),
            source=source,
        )
