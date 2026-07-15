from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class ListingData:
    url: str
    provider: str
    listing_id: str
    distrito: str | None
    concelho: str | None
    tipologia: str | None
    area_bruta_privativa_m2: str | None
    preco_eur: int | float | None
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "provider": self.provider,
            "listing_id": self.listing_id,
            "distrito": self.distrito,
            "concelho": self.concelho,
            "tipologia": self.tipologia,
            "area_bruta_privativa_m2": self.area_bruta_privativa_m2,
            "preco_eur": self.preco_eur,
            "source": self.source,
        }


@dataclass
class ScrapeResult:
    status: Literal["ok", "skipped", "error"]
    url: str
    provider: str | None = None
    data: ListingData | None = None
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "url": self.url,
        }
        if self.provider:
            payload["provider"] = self.provider
        if self.data:
            payload["data"] = self.data.as_dict()
        if self.reason:
            payload["reason"] = self.reason
        return payload
