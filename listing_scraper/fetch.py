from __future__ import annotations

import os

from curl_cffi import requests

from listing_scraper.parsers.base import Provider
from listing_scraper.parsers.common import looks_blocked


class WafBlockedError(RuntimeError):
    pass


def fetch_html_curl(
    url: str,
    *,
    impersonate: str = "chrome131",
    cookie_header: str | None = None,
    timeout: int = 30,
) -> str:
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "pt-PT,pt;q=0.9,en;q=0.8",
    }
    if cookie_header:
        headers["cookie"] = cookie_header

    response = requests.get(
        url,
        impersonate=impersonate,
        headers=headers,
        timeout=timeout,
        allow_redirects=True,
    )
    if looks_blocked(response.text, response.status_code):
        raise WafBlockedError(f"Blocked by anti-bot protection (status={response.status_code})")
    return response.text


def fetch_html_playwright(url: str, provider: Provider, *, timeout_ms: int = 60_000) -> str:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    headless = os.environ.get("LISTING_HEADLESS") == "1"
    ready_expression = provider.playwright_ready_expression()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=headless,
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="pt-PT",
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

        if ready_expression:
            try:
                page.wait_for_function(ready_expression, timeout=timeout_ms)
            except PlaywrightTimeoutError as exc:
                browser.close()
                raise WafBlockedError(
                    "Playwright timed out waiting for listing page content."
                ) from exc

        html = page.content()
        browser.close()

    if looks_blocked(html):
        raise WafBlockedError("Playwright page still appears blocked.")
    return html


def fetch_listing_html(
    url: str,
    provider: Provider,
    *,
    cookie_header: str | None = None,
    use_browser_fallback: bool = True,
) -> tuple[str, str]:
    try:
        return fetch_html_curl(url, cookie_header=cookie_header), "curl_cffi"
    except WafBlockedError:
        if not use_browser_fallback:
            raise
        return fetch_html_playwright(url, provider), "playwright"
