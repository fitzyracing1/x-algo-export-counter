"""Load a batch of candidate or pre-scored rows from JSON, JSONL, or CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path

PRED_PREFIX = "pred_"
FLAG_KEYS = ("in_network", "is_mutual_follow_author", "vqv_eligible", "quoted_vqv_eligible")


def load_records(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"input not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return _load_jsonl(path)
    if suffix == ".json":
        return _load_json(path)
    if suffix == ".csv":
        return _load_csv(path)
    # Peek: JSONL if the first non-comment line starts with { and there is more than one object.
    text = path.read_text(encoding="utf-8")
    stripped = next((ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")), "")
    if stripped.startswith("[") or (stripped.startswith("{") and "\n" not in text.strip()[1:2] and text.lstrip().startswith("[")):
        return _load_json(path)
    if stripped.startswith("{"):
        return _load_jsonl(path)
    raise ValueError(f"{path}: unsupported input type (use .json, .jsonl, or .csv)")


def _load_jsonl(path: Path) -> list[dict]:
    records = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{lineno}: invalid JSONL ({exc})") from exc
        if not isinstance(item, dict):
            raise ValueError(f"{path}:{lineno}: each JSONL line must be an object")
        records.append(_normalize(item))
    if not records:
        raise ValueError(f"{path}: no records")
    return records


def _load_json(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, dict) and "records" in data:
        data = data["records"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError(f"{path}: JSON must be a list, a single object, or {{'records': [...]}}")
    records = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"{path}: record {i} is not an object")
        records.append(_normalize(item))
    if not records:
        raise ValueError(f"{path}: no records")
    return records


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: no records")
    return [_normalize_csv(row) for row in rows]


def _maybe_json(value: str):
    text = value.strip()
    if text.startswith("{") or text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def _normalize_csv(row: dict) -> dict:
    item = {}
    predictions = {}
    flags = {}
    terms = {}
    for key, value in row.items():
        if key is None:
            continue
        if value is None or value == "":
            continue
        key = key.strip()
        parsed = _maybe_json(value) if isinstance(value, str) else value
        if key in ("predictions", "flags", "terms") and isinstance(parsed, dict):
            item[key] = parsed
            continue
        if key.startswith(PRED_PREFIX):
            predictions[key[len(PRED_PREFIX) :]] = float(parsed)
            continue
        if key.startswith("term_"):
            terms[key[5:]] = float(parsed)
            continue
        if key in FLAG_KEYS:
            flags[key] = _as_bool(parsed)
            continue
        item[key] = parsed
    if predictions:
        item.setdefault("predictions", {}).update(predictions)
    if flags:
        item.setdefault("flags", {}).update(flags)
    if terms:
        item.setdefault("terms", {}).update(terms)
    return _normalize(item)


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _normalize(item: dict) -> dict:
    record = dict(item)
    if "id" not in record:
        # Stable fallback so counts can name a row. Not an upstream id.
        record["id"] = record.get("post_id") or record.get("text") or ""
    if "flags" in record and not isinstance(record["flags"], dict):
        raise ValueError(f"record {record.get('id')!r}: flags must be an object")
    if "predictions" in record and not isinstance(record["predictions"], dict):
        raise ValueError(f"record {record.get('id')!r}: predictions must be an object")
    if "terms" in record and not isinstance(record["terms"], dict):
        raise ValueError(f"record {record.get('id')!r}: terms must be an object")
    return record
