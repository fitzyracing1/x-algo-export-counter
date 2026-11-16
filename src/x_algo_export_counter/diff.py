"""Diff two count JSON documents (for example two runs or two weight sets)."""

from __future__ import annotations

import json
from pathlib import Path


def load_counts(path: str | Path) -> dict:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if "stages" not in data:
        raise ValueError(f"{path}: not a counts JSON file (missing 'stages')")
    return data


def _index(rows: list[dict], key: str) -> dict[str, dict]:
    return {str(row[key]): row for row in rows}


def _delta_map(a: dict, b: dict) -> list[dict]:
    keys = list(dict.fromkeys([*a.keys(), *b.keys()]))
    rows = []
    for key in keys:
        left = a.get(key, 0)
        right = b.get(key, 0)
        rows.append({"name": key, "a": left, "b": right, "delta": right - left})
    return rows


def _delta_rows(rows_a: list[dict], rows_b: list[dict], name_key: str, value_key: str = "count") -> list[dict]:
    a = _index(rows_a, name_key)
    b = _index(rows_b, name_key)
    names = list(dict.fromkeys([*a.keys(), *b.keys()]))
    out = []
    for name in names:
        left = a.get(name, {}).get(value_key, 0) or 0
        right = b.get(name, {}).get(value_key, 0) or 0
        out.append({"name": name, "a": left, "b": right, "delta": right - left})
    return out


def diff_counts(a: dict, b: dict) -> dict:
    stages = _delta_map(a.get("stages") or {}, b.get("stages") or {})
    filters = _delta_rows(a.get("filters") or [], b.get("filters") or [], "reason")
    buckets = _delta_rows(a.get("score_buckets") or [], b.get("score_buckets") or [], "bucket")
    heads = _delta_rows(
        a.get("heads_scored") or [],
        b.get("heads_scored") or [],
        "head",
        "total_contribution",
    )
    authors = _delta_rows(
        [
            {"name": row["name"], "count": row.get("exported", 0)}
            for row in a.get("authors") or []
        ],
        [
            {"name": row["name"], "count": row.get("exported", 0)}
            for row in b.get("authors") or []
        ],
        "name",
    )
    sources = _delta_rows(
        [
            {"name": row["name"], "count": row.get("exported", 0)}
            for row in a.get("sources") or []
        ],
        [
            {"name": row["name"], "count": row.get("exported", 0)}
            for row in b.get("sources") or []
        ],
        "name",
    )
    ids_a = set(a.get("exported_ids") or [])
    ids_b = set(b.get("exported_ids") or [])
    return {
        "tool": "x-algo-export-counter",
        "kind": "diff",
        "credit_a": a.get("credit"),
        "credit_b": b.get("credit"),
        "top_n_a": a.get("top_n"),
        "top_n_b": b.get("top_n"),
        "stages": stages,
        "filters": filters,
        "heads_scored": heads,
        "score_buckets": buckets,
        "authors_exported": authors,
        "sources_exported": sources,
        "exported_only_in_a": sorted(ids_a - ids_b),
        "exported_only_in_b": sorted(ids_b - ids_a),
        "exported_in_both": sorted(ids_a & ids_b),
    }


def render_diff(diff: dict) -> str:
    def table(title: str, rows: list[dict]) -> list[str]:
        lines = [f"## {title}", "", "| name | a | b | delta |", "|---|---:|---:|---:|"]
        if not rows:
            lines.append("| (none) |  |  |  |")
        for row in rows:
            delta = row["delta"]
            if isinstance(delta, float):
                d = f"{delta:+.6f}"
                av, bv = f"{row['a']:.6f}", f"{row['b']:.6f}"
            else:
                d = f"{delta:+d}" if isinstance(delta, int) else str(delta)
                av, bv = str(row["a"]), str(row["b"])
            lines.append(f"| {row['name']} | {av} | {bv} | {d} |")
        lines.append("")
        return lines

    lines = [
        "# X algorithm export-count diff",
        "",
        f"A: {diff.get('credit_a') or '(counts A)'}",
        f"B: {diff.get('credit_b') or '(counts B)'}",
        "",
    ]
    lines += table("Stages", diff["stages"])
    lines += table("Filters", diff["filters"])
    lines += table("Head contributions (scored)", [r for r in diff["heads_scored"] if r["delta"] or r["a"] or r["b"]])
    lines += table("Score buckets", diff["score_buckets"])
    lines += table("Exported by source", diff["sources_exported"])
    lines += table("Exported by author", diff["authors_exported"])
    lines += [
        "## Exported-set membership",
        "",
        f"- only in A ({len(diff['exported_only_in_a'])}): {', '.join(diff['exported_only_in_a']) or '(none)'}",
        f"- only in B ({len(diff['exported_only_in_b'])}): {', '.join(diff['exported_only_in_b']) or '(none)'}",
        f"- in both ({len(diff['exported_in_both'])}): {', '.join(diff['exported_in_both']) or '(none)'}",
        "",
    ]
    return "\n".join(lines)


def write_diff(diff: dict, out: str | Path) -> Path:
    out = Path(out)
    if out.suffix.lower() == ".md":
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_diff(diff), encoding="utf-8")
        return out
    if out.suffix.lower() == ".json":
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8")
        return out
    out.mkdir(parents=True, exist_ok=True)
    (out / "diff.json").write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8")
    (out / "diff.md").write_text(render_diff(diff), encoding="utf-8")
    return out
