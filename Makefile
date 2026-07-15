.PHONY: help setup install-deps check-deps venv deps browsers playwright-deps scrape test batch browser-only clean

PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin
PY := $(BIN)/python
PIP := $(BIN)/pip
PLAYWRIGHT := $(BIN)/playwright

APT_PACKAGES := python3 python3-venv xvfb
URL ?= https://www.properstar.pt/anuncio/117349150
URLS ?= sample_urls.txt

help:
	@echo "Portuguese listing scraper (Ubuntu)"
	@echo ""
	@echo "Targets:"
	@echo "  make setup          Install system deps, venv, Python packages, Chromium"
	@echo "  make check-deps     Show missing Ubuntu packages (no sudo)"
	@echo "  make scrape URL=... Scrape one listing URL"
	@echo "  make batch URLS=... Scrape many URLs (invalid ones are skipped)"
	@echo "  make test           Scrape the default Properstar example"
	@echo "  make browser-only URL=... Force Playwright (skip curl)"
	@echo "  make clean          Remove the virtual environment"
	@echo ""
	@echo "Supported portals:"
	@echo "  properstar.pt, idealista.pt, imovirtual.com (+ generic JSON-LD fallback)"
	@echo ""
	@echo "Optional env vars:"
	@echo "  LISTING_COOKIE            Browser cookies for curl fast path"
	@echo "  LISTING_BROWSER_ONLY=1    Same as: make browser-only"
	@echo "  LISTING_HEADLESS=1        Force headless Playwright (often blocked)"

setup: install-deps venv deps browsers playwright-deps
	@echo ""
	@echo "Ready. Try:"
	@echo "  make test"
	@echo "  make scrape URL=https://www.imovirtual.com/pt/anuncio/apartamento-t2-para-venda-ID1i2AO"
	@echo "  make batch URLS=sample_urls.txt"

check-deps:
	@missing=""; \
	for pkg in $(APT_PACKAGES); do \
		if ! dpkg -s "$$pkg" >/dev/null 2>&1; then \
			missing="$$missing $$pkg"; \
		fi; \
	done; \
	if [ -z "$$missing" ]; then \
		echo "All system packages already installed."; \
	else \
		echo "Missing packages:$$missing"; \
		exit 1; \
	fi

install-deps:
	@missing=""; \
	for pkg in $(APT_PACKAGES); do \
		if ! dpkg -s "$$pkg" >/dev/null 2>&1; then \
			missing="$$missing $$pkg"; \
		fi; \
	done; \
	if [ -z "$$missing" ]; then \
		echo "System packages already installed."; \
		exit 0; \
	fi; \
	echo "Installing:$$missing"; \
	if sudo apt-get install -y $$missing; then \
		exit 0; \
	fi; \
	echo ""; \
	echo "Install failed. Trying apt-get update..."; \
	if sudo apt-get update && sudo apt-get install -y $$missing; then \
		exit 0; \
	fi; \
	echo ""; \
	echo "apt still failed. If a third-party apt repo is broken, fix or remove it first."; \
	exit 1

venv:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)

deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

browsers: deps
	$(PLAYWRIGHT) install chromium

playwright-deps: browsers
	$(PY) -m playwright install-deps chromium

scrape: deps browsers
	$(PY) scrape_listing.py "$(URL)"

batch: deps browsers
	$(PY) scrape_listing.py --file "$(URLS)"

test: scrape

browser-only: deps browsers
	LISTING_BROWSER_ONLY=1 $(PY) scrape_listing.py "$(URL)"

clean:
	rm -rf $(VENV)
