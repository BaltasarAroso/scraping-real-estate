from __future__ import annotations

import re

from listing_scraper.models import ListingData
from listing_scraper.parsers.base import Provider
from listing_scraper.parsers.common import (
    html_to_text,
    parse_area_from_text,
    parse_price_number,
    parse_tipologia,
)

LISTING_RE = re.compile(r"/imovel/(\d+)", re.I)
AGENCY_LISTING_RE = re.compile(r"/pro/[^/]+/imovel/(\d+)", re.I)


class IdealistaProvider(Provider):
    name = "idealista"

    def matches(self, url: str) -> bool:
        lowered = url.lower()
        return "idealista.pt" in lowered and (
            LISTING_RE.search(url) or AGENCY_LISTING_RE.search(url)
        )

    def listing_id(self, url: str) -> str:
        for pattern in (AGENCY_LISTING_RE, LISTING_RE):
            match = pattern.search(url)
            if match:
                return match.group(1)
        raise ValueError("Invalid Idealista listing URL")

    def playwright_ready_expression(self) -> str | None:
        return (
            "() => !!document.querySelector('h1') && "
            "!/^idealista\\.pt$/i.test(document.title || '')"
        )

    def parse(self, url: str, html: str, *, source: str) -> ListingData:
        text = html_to_text(html)
        title_match = re.search(
            r"(Apartamento|Moradia|Duplex|Loft|Estúdio)\s+(T\d+)",
            text,
            re.I,
        )
        title = title_match.group(0) if title_match else ""
        if not title:
            raise ValueError("Idealista listing page not loaded (captcha or invalid URL)")

        price_match = re.search(r"([\d.]+)\s*€", text)
        area = parse_area_from_text(text)
        distrito = None
        concelho = None

        location_block = re.search(
            r"## Localização\s+(.+?)(?:\n## |\Z)",
            text,
            flags=re.S,
        )
        if location_block:
            lines = [
                line.strip(" *")
                for line in location_block.group(1).splitlines()
                if line.strip(" *")
            ]
            if lines:
                last = lines[-1]
                if "," in last:
                    parts = [part.strip() for part in last.split(",")]
                    if len(parts) >= 2:
                        concelho = parts[0]
                        distrito = parts[1]
                else:
                    concelho = last

        return ListingData(
            url=url,
            provider=self.name,
            listing_id=self.listing_id(url),
            distrito=distrito,
            concelho=concelho,
            tipologia=parse_tipologia(title, text),
            area_bruta_privativa_m2=area,
            preco_eur=parse_price_number(price_match.group(1) if price_match else None),
            source=source,
        )
