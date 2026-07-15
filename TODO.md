# TODO

## Idealista access

- [ ] Request access to the official Idealista Search API and prefer it over page scraping.
- [ ] Test Browserless's free tier as an Idealista-only fallback using its supported Playwright connection and proxy features.
- [ ] If Browserless is unreliable, evaluate Browserbase Developer before higher-cost scraping APIs.
- [ ] Keep local Playwright for Properstar and `curl_cffi` for Imovirtual while those paths remain reliable.
- [ ] Never automate CAPTCHA interaction or add fingerprint-evasion code. If a challenge is shown, stop, skip the URL, use an approved API, or require manual intervention.

## Legal and compliance

- [ ] Review and document each provider's current Terms of Service, robots policy, API terms, and applicable database/copyright restrictions before production use.
- [ ] Obtain legal review for the intended jurisdiction and commercial use case. This repository does not constitute legal advice or guarantee compliance.
- [ ] Collect only the fields required for the stated purpose; avoid personal contact details and other unnecessary personal data.
- [ ] Define retention, deletion, access-control, and data-subject-request procedures where GDPR or other privacy law applies.
- [ ] Use conservative request rates, caching, backoff, and per-provider limits; do not interfere with site operation.
- [ ] Record provenance, retrieval time, provider, and lawful basis/permission for stored records.
- [ ] Add a provider kill switch and disable collection promptly when permission, terms, or legal status changes.

## Engineering

- [ ] Add explicit provider configuration for rate limits, timeouts, retries, and circuit breakers.
- [ ] Add fixtures and parser tests that do not repeatedly request production websites.
- [ ] Add structured metrics for `ok`, `skipped`, `blocked`, and `error` outcomes without logging cookies or secrets.
- [ ] Add secret scanning and dependency/security checks to CI.
