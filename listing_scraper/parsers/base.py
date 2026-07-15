from __future__ import annotations

import re
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from listing_scraper.models import ListingData


class Provider(ABC):
    name: str

    @abstractmethod
    def matches(self, url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def listing_id(self, url: str) -> str:
        raise NotImplementedError

    def playwright_ready_expression(self) -> str | None:
        return None

    @abstractmethod
    def parse(self, url: str, html: str, *, source: str) -> ListingData:
        raise NotImplementedError

    def hostnames(self) -> set[str]:
        return set()


def host_from_url(url: str) -> str:
    host = urlparse(url).hostname or ""
    return host.lower()
