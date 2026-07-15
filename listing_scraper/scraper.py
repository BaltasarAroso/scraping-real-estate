from __future__ import annotations

import os

from listing_scraper.fetch import WafBlockedError, fetch_listing_html
from listing_scraper.models import ListingData, ScrapeResult
from listing_scraper.registry import provider_for_url
from listing_scraper.security import validate_listing_url


def scrape_url(
    url: str,
    *,
    cookie_header: str | None = None,
    use_browser_fallback: bool = True,
    browser_only: bool = False,
) -> ScrapeResult:
    normalized, reason = validate_listing_url(url)
    if reason:
        return ScrapeResult(status="skipped", url=url, reason=reason)

    assert normalized is not None
    provider = provider_for_url(normalized)
    if not provider:
        return ScrapeResult(
            status="skipped",
            url=normalized,
            reason="unsupported_provider",
        )

    try:
        if browser_only:
            from listing_scraper.fetch import fetch_html_playwright

            html = fetch_html_playwright(normalized, provider)
            transport = "playwright"
        else:
            html, transport = fetch_listing_html(
                normalized,
                provider,
                cookie_header=cookie_header,
                use_browser_fallback=use_browser_fallback,
            )
        data = provider.parse(
            normalized,
            html,
            source=f"{transport}+{provider.name}",
        )
        return ScrapeResult(
            status="ok",
            url=normalized,
            provider=provider.name,
            data=data,
        )
    except (WafBlockedError, ValueError) as exc:
        return ScrapeResult(
            status="error",
            url=normalized,
            provider=provider.name,
            reason=str(exc),
        )


def scrape_urls(
    urls: list[str],
    *,
    cookie_header: str | None = None,
    use_browser_fallback: bool = True,
    browser_only: bool = False,
) -> list[ScrapeResult]:
    results: list[ScrapeResult] = []
    for url in urls:
        url = url.strip()
        if not url or url.startswith("#"):
            continue
        results.append(
            scrape_url(
                url,
                cookie_header=cookie_header,
                use_browser_fallback=use_browser_fallback,
                browser_only=browser_only,
            )
        )
    return results


def default_cookie_header() -> str | None:
    return os.environ.get("LISTING_COOKIE") or os.environ.get("PROPERSTAR_COOKIE")
