#!/usr/bin/env python3
"""Backward-compatible entrypoint for Properstar URLs."""

from scrape_listing import main

if __name__ == "__main__":
    raise SystemExit(main())
