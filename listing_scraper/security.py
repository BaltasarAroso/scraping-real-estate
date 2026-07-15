from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse, urlunparse

MAX_URL_LENGTH = 2048

ALLOWED_HOSTS = {
    "properstar.pt",
    "www.properstar.pt",
    "idealista.pt",
    "www.idealista.pt",
    "imovirtual.com",
    "www.imovirtual.com",
    "casa.sapo.pt",
    "www.casa.sapo.pt",
    "supercasa.pt",
    "www.supercasa.pt",
}

LISTING_PATH_PATTERNS = (
    re.compile(r"/anuncio/\d+", re.I),  # properstar
    re.compile(r"/imovel/\d+", re.I),  # idealista
    re.compile(r"/pro/[^/]+/imovel/\d+", re.I),  # idealista agency
    re.compile(r"/pt/anuncio/.+-ID[\w-]+", re.I),  # imovirtual
    re.compile(r"/(comprar|arrendar)-[^/]+/[^/]+-\d+", re.I),  # casa.sapo (best effort)
)


def _hostname_allowed(hostname: str) -> bool:
    host = hostname.lower().rstrip(".")
    if host in ALLOWED_HOSTS:
        return True
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in ALLOWED_HOSTS)


def _hostname_is_public(hostname: str) -> bool:
    host = hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return True
    return ip.is_global


def normalize_url(url: str) -> tuple[str | None, str | None]:
    if not url or not isinstance(url, str):
        return None, "empty_url"

    candidate = url.strip()
    if not candidate:
        return None, "empty_url"
    if len(candidate) > MAX_URL_LENGTH:
        return None, "url_too_long"

    parsed = urlparse(candidate)
    if parsed.scheme not in {"https"}:
        return None, "https_required"
    if parsed.username or parsed.password:
        return None, "credentials_not_allowed"
    if not parsed.hostname:
        return None, "missing_hostname"
    if not _hostname_is_public(parsed.hostname):
        return None, "private_or_local_host"
    if not _hostname_allowed(parsed.hostname):
        return None, "host_not_allowed"

    normalized = urlunparse(
        (
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path or "/",
            "",
            parsed.query,
            "",
        )
    )
    return normalized, None


def is_listing_path(path: str) -> bool:
    return any(pattern.search(path) for pattern in LISTING_PATH_PATTERNS)


def validate_listing_url(url: str) -> tuple[str | None, str | None]:
    normalized, reason = normalize_url(url)
    if reason:
        return None, reason
    assert normalized is not None
    path = urlparse(normalized).path
    if not is_listing_path(path):
        return None, "unsupported_listing_path"
    return normalized, None
