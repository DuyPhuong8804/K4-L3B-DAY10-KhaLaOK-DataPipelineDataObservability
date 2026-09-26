from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import html
from pathlib import Path
import re
import time

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

CROSSREF_WORKS_URL = "https://api.crossref.org/works"
USER_AGENT = "K4-L3B-Day10-DataObservabilityLab/0.1 (student lab; python-requests)"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4
REQUEST_TIMEOUT_SECONDS = 30
PUBLISHED_DATE_KEYS = ("published", "published-online", "published-print", "issued", "created")

_MARKUP_TAG = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(value: str | list[str] | None) -> str:
    if isinstance(value, list):
        value = value[0] if value else ""
    # Tags are removed before unescaping so escaped "&lt;...&gt;" in prose survives as text.
    return normalize_whitespace(html.unescape(_MARKUP_TAG.sub(" ", value or "")))


def _date_from_parts(date_obj: dict | None) -> str | None:
    parts = (date_obj or {}).get("date-parts") or []
    first = parts[0] if parts else []
    if not first or first[0] is None:
        return None
    year, month, day = (list(first) + [1, 1])[:3]
    return date(int(year), int(month or 1), int(day or 1)).isoformat()


def _date_from_timestamp(date_obj: dict | None) -> str | None:
    stamp = (date_obj or {}).get("date-time")
    return stamp[:10] if stamp else None


def _published_date(item: dict) -> str | None:
    for key in PUBLISHED_DATE_KEYS:
        value = _date_from_parts(item.get(key))
        if value:
            return value
    return None


def _author_names(authors: list[dict] | None) -> list[str]:
    names = []
    for author in authors or []:
        name = normalize_whitespace(" ".join(p for p in (author.get("given"), author.get("family")) if p))
        name = name or normalize_whitespace(author.get("name") or "")
        if name:
            names.append(name)
    return names


def _unique(values: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        cleaned = normalize_whitespace(value or "")
        if cleaned:
            seen.setdefault(cleaned, None)
    return list(seen)


def _pdf_url(item: dict, fallback: str) -> str:
    for link in item.get("link") or []:
        if "pdf" in (link.get("content-type") or "").lower() and link.get("URL"):
            return link["URL"]
    return fallback


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records: list[PaperRecord] = []
    for item in payload.get("message", {}).get("items", []):
        doi = normalize_whitespace(item.get("DOI") or "").lower()
        title = _clean_text(item.get("title"))
        summary = _clean_text(item.get("abstract"))
        published = _published_date(item)
        if not (doi and title and summary and published):
            continue

        categories = _unique(item.get("subject") or [])
        abs_url = item.get("URL") or f"https://doi.org/{doi}"
        updated = (
            _date_from_timestamp(item.get("deposited"))
            or _date_from_timestamp(item.get("created"))
            or published
        )
        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=_author_names(item.get("author")),
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=_pdf_url(item, abs_url),
                comment=f"Crossref record {doi}",
            )
        )
    return records


def _retry_delay(response: requests.Response | None, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After") if response is not None else None
    if retry_after and retry_after.isdigit():
        return min(float(retry_after), 60.0)
    return float(2**attempt)


def _request_crossref(settings: Settings) -> dict | None:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = None
        try:
            response = requests.get(
                CROSSREF_WORKS_URL,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            print(f"[crossref] attempt {attempt}/{MAX_ATTEMPTS} network error: {exc}")
        else:
            if response.status_code == 200:
                payload = response.json()
                if payload.get("message", {}).get("items"):
                    return payload
                print("[crossref] API returned no items.")
                return None
            if response.status_code not in RETRYABLE_STATUS:
                print(f"[crossref] non-retryable HTTP {response.status_code}.")
                return None
            print(f"[crossref] attempt {attempt}/{MAX_ATTEMPTS} got HTTP {response.status_code}.")
        if attempt < MAX_ATTEMPTS:
            time.sleep(_retry_delay(response, attempt))
    return None


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    snapshot = settings.paths.raw_api_response
    payload = None
    if settings.refresh_source or not snapshot.exists():
        payload = _request_crossref(settings)
        if payload is not None:
            write_json(snapshot, payload)
            print(f"[crossref] fetched live payload from {settings.source_api} -> {snapshot.name}")

    if payload is None:
        if not snapshot.exists():
            raise RuntimeError(f"Crossref API unavailable and no local snapshot at {snapshot}.")
        print(f"[crossref] using local snapshot {snapshot.name}")
        payload = read_json(snapshot)

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    return [PaperRecord(**row) for row in read_json(path)]
