#!/usr/bin/env python3
"""Scrape Portuguese real-estate listing URLs from multiple portals."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from listing_scraper.scraper import default_cookie_header, scrape_url, scrape_urls


def _read_urls(args: argparse.Namespace) -> list[str]:
    if args.url:
        return [args.url]
    if args.file:
        return Path(args.file).read_text(encoding="utf-8").splitlines()
    if not sys.stdin.isatty():
        return sys.stdin.read().splitlines()
    return []


def _reexec_under_xvfb_if_needed() -> None:
    if os.environ.get("LISTING_XVFB") == "1":
        return
    if os.name != "posix" or os.environ.get("DISPLAY"):
        return
    xvfb_run = shutil.which("xvfb-run")
    if not xvfb_run:
        return

    env = os.environ.copy()
    env["LISTING_XVFB"] = "1"
    os.execve(xvfb_run, [xvfb_run, "-a", sys.executable, *sys.argv], env)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scrape listing data from supported Portuguese real-estate portals.",
    )
    parser.add_argument("url", nargs="?", help="Single listing URL")
    parser.add_argument(
        "-f",
        "--file",
        help="Text file with one URL per line (invalid URLs are skipped)",
    )
    parser.add_argument(
        "--browser-only",
        action="store_true",
        help="Skip curl and always use Playwright",
    )
    parser.add_argument(
        "--no-browser-fallback",
        action="store_true",
        help="Do not fall back to Playwright when curl is blocked",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any URL is skipped or errors",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    _reexec_under_xvfb_if_needed()
    parser = build_parser()
    args = parser.parse_args(argv)
    urls = _read_urls(args)
    if not urls:
        parser.print_help()
        return 2

    cookie_header = default_cookie_header()
    browser_only = args.browser_only or os.environ.get("LISTING_BROWSER_ONLY") == "1"
    use_browser_fallback = not args.no_browser_fallback

    if len(urls) == 1 and args.url:
        result = scrape_url(
            urls[0],
            cookie_header=cookie_header,
            use_browser_fallback=use_browser_fallback,
            browser_only=browser_only,
        )
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        if args.strict and result.status != "ok":
            return 1
        return 0

    results = scrape_urls(
        urls,
        cookie_header=cookie_header,
        use_browser_fallback=use_browser_fallback,
        browser_only=browser_only,
    )
    for result in results:
        print(json.dumps(result.as_dict(), ensure_ascii=False))

    if args.strict and any(result.status != "ok" for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
