from __future__ import annotations

import json
import re
from typing import Any

TIPOLOGIA_RE = re.compile(r"\bT\d+\b", re.I)
AREA_BRUTA_PRIVATIVA_RE = re.compile(
    r"Área bruta privativa\s*\n?\s*([\d\s.,]+)\s*m²",
    re.I,
)
AREA_BRUTA_RE = re.compile(
    r"Área bruta\s*\n?\s*([\d\s.,]+)\s*m²",
    re.I,
)
AREA_BRUTA_INLINE_RE = re.compile(
    r"([\d\s.,]+)\s*m²\s*área bruta",
    re.I,
)


def html_to_text(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"\n+", "\n", text)
    return text


def parse_json_ld_blocks(html: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for raw in re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        flags=re.I | re.S,
    ):
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            blocks.append(data)
        elif isinstance(data, list):
            blocks.extend(item for item in data if isinstance(item, dict))
    return blocks


def find_json_ld(html: str, *types: str) -> dict[str, Any] | None:
    wanted = {t.lower() for t in types}
    for block in parse_json_ld_blocks(html):
        block_type = str(block.get("@type", "")).lower()
        if block_type in wanted:
            return block
        graph = block.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict) and str(item.get("@type", "")).lower() in wanted:
                    return item
    return None


def parse_next_data(html: str) -> dict[str, Any] | None:
    match = re.search(
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        flags=re.I | re.S,
    )
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def normalize_distrito(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.replace("-Distrito", "").strip()
    cleaned = re.sub(r"\s*\(Ilha\)\s*$", "", cleaned, flags=re.I)
    return cleaned or None


def parse_tipologia(*sources: str, bedrooms: int | None = None) -> str | None:
    for source in sources:
        match = TIPOLOGIA_RE.search(source or "")
        if match:
            return match.group(0).upper()
    if bedrooms is not None:
        return f"T{bedrooms}"
    return None


def parse_area_from_text(text: str) -> str | None:
    for pattern in (AREA_BRUTA_PRIVATIVA_RE, AREA_BRUTA_RE, AREA_BRUTA_INLINE_RE):
        match = pattern.search(text)
        if match:
            return re.sub(r"[\s.]", "", match.group(1)).replace(",", ".")
    return None


def parse_area_from_html(html: str) -> str | None:
    return parse_area_from_text(html_to_text(html))


def parse_price_number(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        for key in ("value", "salePrice", "price"):
            if key in value:
                return parse_price_number(value[key])
        if "salePrice" in value and isinstance(value["salePrice"], dict):
            return parse_price_number(value["salePrice"].get("value"))
    text = str(value)
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def looks_blocked(html: str, status_code: int = 200) -> bool:
    lowered = html.lower()
    return (
        status_code in {403, 429}
        or "azure waf" in lowered
        or "checking you're not a bot" in lowered
        or "the request is blocked" in lowered
        or "captcha" in lowered and "idealista" in lowered
    )
