# Real-estate listing scraper

Extract normalized data from Portuguese real-estate listing URLs.

Currently supported:

- Properstar
- Imovirtual
- Idealista (parser included, but access may be blocked by CAPTCHA)
- Generic JSON-LD fallback for approved hosts

Extracted fields:

- distrito
- concelho
- tipologia
- área bruta / área bruta privativa when available
- preço

The scraper tries `curl_cffi` first and can fall back to Playwright when JavaScript or anti-bot checks require a browser.

## Ubuntu setup

Requirements:

- Ubuntu
- Python 3
- `make`
- `sudo` access for the initial system-package installation

```bash
git clone git@github.com:BaltasarAroso/scraping-real-estate.git
cd scraping-real-estate
make setup
make test
```

`make setup` installs:

- `python3`
- `python3-venv`
- `xvfb`
- Python dependencies
- Playwright Chromium and its system dependencies

## Command-line usage

Scrape one URL:

```bash
make scrape URL="https://www.properstar.pt/anuncio/117349150"
```

Or call Python directly:

```bash
.venv/bin/python scrape_listing.py \
  "https://www.imovirtual.com/pt/anuncio/apartamento-t2-para-venda-ID1i2AO"
```

Scrape a file containing one URL per line:

```bash
make batch URLS=sample_urls.txt
```

You can also pipe URLs through standard input:

```bash
printf '%s\n' \
  "https://www.properstar.pt/anuncio/117349150" \
  "https://www.imovirtual.com/pt/anuncio/apartamento-t2-para-venda-ID1i2AO" \
  | .venv/bin/python scrape_listing.py
```

Use `--strict` when skipped or failed URLs should produce a non-zero exit code:

```bash
.venv/bin/python scrape_listing.py --strict "https://example.com/not-allowed"
```

## Output

A successful result looks like:

```json
{
  "status": "ok",
  "url": "https://www.properstar.pt/anuncio/117349150",
  "provider": "properstar",
  "data": {
    "url": "https://www.properstar.pt/anuncio/117349150",
    "provider": "properstar",
    "listing_id": "117349150",
    "distrito": "Porto",
    "concelho": "Maia",
    "tipologia": "T3",
    "area_bruta_privativa_m2": "146",
    "preco_eur": 120000,
    "source": "playwright+properstar"
  }
}
```

Each result has one of these statuses:

- `ok`: extraction succeeded
- `skipped`: the URL failed validation or the provider is unsupported
- `error`: the URL was valid, but loading or parsing failed

Missing listing fields are returned as `null`.

## Use it from another Python application

Install this repository in the same application environment, then import the library:

```python
from listing_scraper import scrape_url

result = scrape_url(
    "https://www.imovirtual.com/pt/anuncio/apartamento-t2-para-venda-ID1i2AO"
)

if result.status == "ok":
    listing = result.data
    print(listing.preco_eur, listing.concelho)
elif result.status == "skipped":
    print("Ignored:", result.reason)
else:
    print("Failed:", result.reason)
```

For multiple URLs:

```python
from listing_scraper import scrape_urls

results = scrape_urls([
    "https://www.properstar.pt/anuncio/117349150",
    "https://www.imovirtual.com/pt/anuncio/apartamento-t2-para-venda-ID1i2AO",
])
```

Do not pass unvalidated URLs directly to a separate HTTP client. `scrape_url()` performs the project's host, scheme, and listing-path validation before fetching.

## Add an HTTP API

The repository currently provides a Python library and CLI, not a public HTTP service. A small FastAPI wrapper can expose it to another website:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from listing_scraper import scrape_url

app = FastAPI()


class ScrapeRequest(BaseModel):
    url: HttpUrl


@app.post("/scrape")
def scrape(request: ScrapeRequest):
    result = scrape_url(str(request.url))
    payload = result.as_dict()

    if result.status == "skipped":
        raise HTTPException(status_code=400, detail=payload)
    if result.status == "error":
        raise HTTPException(status_code=502, detail=payload)
    return payload
```

Install and run the additional API dependencies:

```bash
.venv/bin/pip install fastapi uvicorn
xvfb-run -a .venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
```

The `xvfb-run` wrapper is required on a Linux server without a graphical display when Playwright fallback is enabled. For production, also add authentication, request quotas, body-size limits, timeouts, structured logging, and a job queue. Do not expose cookies or provider credentials to API clients.

## Vercel and other serverless websites

Running the full scraper directly inside a typical Vercel function is not recommended:

- Properstar currently needs a headed Playwright browser under `xvfb`.
- Browser binaries and system packages increase deployment size.
- Browser startup can exceed serverless execution limits.
- Concurrent requests can exhaust memory quickly.

Recommended architecture:

```text
Vercel website
      |
      | authenticated HTTPS request
      v
Scraper API / worker on Ubuntu, a container platform, or browser service
      |
      v
Properstar / Imovirtual / approved provider API
```

Deploy the scraper backend to an environment that supports Chromium and `xvfb`, such as:

- an Ubuntu VPS
- a long-running container service
- a background worker
- a browser-as-a-service provider

The Vercel frontend or server route should call that backend. Keep the backend private or require an API key, and never place scraper cookies in browser-side JavaScript.

For providers that work through `curl_cffi`, a browser-free serverless endpoint may work with:

```python
result = scrape_url(url, use_browser_fallback=False)
```

This mode will return an error rather than launching Playwright when a provider blocks the HTTP request.

## Environment variables

No environment variables are required for normal Ubuntu usage.

- `LISTING_COOKIE`: optional cookie header for the HTTP fast path
- `LISTING_BROWSER_ONLY=1`: skip `curl_cffi` and always use Playwright
- `LISTING_HEADLESS=1`: force headless Playwright; some providers may block it
- `LISTING_XVFB=1`: internal flag set automatically after relaunching under `xvfb`

Store secrets in the deployment platform's secret manager. Never commit `.env` files or cookies.

## URL security

URLs are validated before any network request. The scraper:

- requires HTTPS
- rejects embedded usernames and passwords
- rejects localhost and literal private IP addresses
- accepts only configured provider hosts
- requires a recognized listing path
- skips invalid URLs instead of fetching them

This reduces SSRF risk but does not replace network-level egress restrictions. A public deployment should also prevent outbound access to private networks at the firewall or platform level and keep the provider allowlist narrow.

## Legal and responsible use

Before production use:

- review each provider's current Terms of Service, robots policy, and API terms
- prefer official APIs or feeds
- collect only fields required for the stated purpose
- avoid unnecessary personal data
- use conservative request rates, caching, and backoff
- stop when CAPTCHA or another explicit access restriction is shown
- obtain legal review for the intended jurisdiction and commercial use case

Do not add automated CAPTCHA interaction or fingerprint-evasion code. This project does not provide legal advice or guarantee that a particular use is lawful. See [TODO.md](TODO.md) for the compliance and engineering checklist.

## Development commands

```bash
make help
make check-deps
make browser-only URL="https://www.properstar.pt/anuncio/117349150"
make clean
```

## Known limitations

- Portal markup and embedded data structures can change without notice.
- “Área bruta” is not always the same legal/registry concept as “área bruta privativa”.
- Idealista may block datacenter IPs or display CAPTCHA.
- Removed, expired, login-only, or malformed listings return `error` or `skipped`.
- Generic JSON-LD extraction only works for hosts and paths permitted by the security allowlist.
