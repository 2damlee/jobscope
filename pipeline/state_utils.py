import hashlib
import json
from datetime import date


def build_source_hash(
    *,
    title,
    company,
    location,
    category,
    seniority,
    description,
    date_posted,
    url,
) -> str:
    payload = {
        "title": title,
        "company": company,
        "location": location,
        "category": category,
        "seniority": seniority,
        "description": description,
        "date_posted": date_posted.isoformat() if isinstance(date_posted, date) else date_posted,
        "url": url,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def has_source_changed(existing_hash: str | None, new_hash: str) -> bool:
    return existing_hash != new_hash