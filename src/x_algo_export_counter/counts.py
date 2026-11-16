"""Aggregate stage, filter, head, bucket, author, source, and top-N counts."""

from __future__ import annotations

from collections import Counter, defaultdict

from x_algo_export_counter.citations import (
    SCORE_BUCKETS,
    SOURCES,
    STAGES,
    UNAPPLIED_SCORE_ADJUSTMENTS,
    UPSTREAM_COMMIT,
    UPSTREAM_COMMIT_DATE,
    UPSTREAM_REPO,
    filter_citation,
    source_citation,
)
from x_algo_export_counter.scorer import ALL_HEADS, credit_line


def _bucket_label(score: float) -> str:
    for label, lo, hi in SCORE_BUCKETS:
        if lo is None and score < hi:
            return label
        if hi is None and score >= lo:
            return label
        if lo is not None and hi is not None and lo <= score < hi:
            return label
    return SCORE_BUCKETS[-1][0]


def _group_counts(rows: list[dict], key: str) -> list[dict]:
    counter = Counter((row.get(key) or "unspecified") for row in rows)
    return [{"name": name, "count": count} for name, count in counter.most_common()]


def _author_source_table(rows_by_stage: dict[str, list[dict]], key: str) -> list[dict]:
    names = set()
    for rows in rows_by_stage.values():
        for row in rows:
            names.add(row.get(key) or "unspecified")
    table = []
    for name in sorted(names, key=lambda n: (-sum(1 for r in rows_by_stage.get("exported", []) if (r.get(key) or "unspecified") == n), n)):
        entry = {"name": name}
        if key == "source":
            entry["citation"] = source_citation(name)
            entry["known_source"] = name in SOURCES
        for stage, rows in rows_by_stage.items():
            entry[stage] = sum(1 for r in rows if (r.get(key) or "unspecified") == name)
        table.append(entry)
    return table


def _head_contributions(rows: list[dict]) -> list[dict]:
    totals: dict[str, float] = defaultdict(float)
    abs_totals: dict[str, float] = defaultdict(float)
    n = len(rows)
    heads = set(ALL_HEADS)
    for row in rows:
        for head, value in (row.get("terms") or {}).items():
            totals[head] += float(value)
            abs_totals[head] += abs(float(value))
            heads.add(head)
    abs_sum = sum(abs_totals.values()) or 1.0
    out = []
    for head in sorted(heads, key=lambda h: -abs(totals[h])):
        total = totals.get(head, 0.0)
        out.append(
            {
                "head": head,
                "total_contribution": total,
                "mean_contribution": (total / n) if n else 0.0,
                "share_of_abs_total": abs_totals.get(head, 0.0) / abs_sum,
            }
        )
    return out


def build_counts(result: dict, *, top_n_report: int | None = None) -> dict:
    candidates = result["candidates"]
    pre_dropped = result["pre_dropped"]
    scored = result["scored"]
    selected = result["selected"]
    not_selected = result["not_selected"]
    post_dropped = result["post_dropped"]
    exported = result["exported"]
    config = result["config"]

    stages = {
        "candidates_in": len(candidates),
        "pre_scoring_filtered": len(pre_dropped),
        "scored": len(scored),
        "selected": len(selected),
        "not_selected_top_k": len(not_selected),
        "post_selection_filtered": len(post_dropped),
        "exported": len(exported),
    }

    filter_counter: Counter[str] = Counter()
    filter_rows = []
    for row in pre_dropped + post_dropped:
        reason = row["dropped_by"]
        filter_counter[reason] += 1
    for reason, count in filter_counter.most_common():
        stage = next(r["dropped_stage"] for r in (pre_dropped + post_dropped) if r["dropped_by"] == reason)
        filter_rows.append(
            {
                "reason": reason,
                "stage": stage,
                "count": count,
                "known_filter": any(r["dropped_by"] == reason and r.get("known_filter") for r in (pre_dropped + post_dropped)),
                "citation": filter_citation(reason),
            }
        )

    report_n = top_n_report or result.get("top_n") or min(10, len(exported))
    top_rows = []
    for row in exported[:report_n]:
        top_rows.append(
            {
                "rank": row.get("rank"),
                "id": row.get("id"),
                "author": row.get("author") or "unspecified",
                "source": row.get("source") or "unspecified",
                "final_score": row.get("final_score"),
                "weighted_sum": row.get("weighted_sum"),
                "text": (row.get("text") or "")[:120],
            }
        )

    buckets = []
    bucket_counts = Counter(_bucket_label(r["final_score"]) for r in scored)
    for label, lo, hi in SCORE_BUCKETS:
        buckets.append({"bucket": label, "count": bucket_counts.get(label, 0), "lo": lo, "hi": hi})

    by_stage = {
        "candidates_in": candidates,
        "scored": scored,
        "exported": exported,
    }

    counts = {
        "tool": "x-algo-export-counter",
        "version": "0.1.0",
        "credit": credit_line(config),
        "upstream": {
            "repo": UPSTREAM_REPO,
            "commit": UPSTREAM_COMMIT,
            "commit_date": UPSTREAM_COMMIT_DATE,
        },
        "top_n": result.get("top_n"),
        "top_n_applied": result.get("top_n_applied"),
        "unapplied": list(UNAPPLIED_SCORE_ADJUSTMENTS),
        "notes": [
            "This is a local count over the input batch, not a live X feed.",
            "Score buckets are a reporting convention of this tool, not upstream thresholds.",
            "Default predicted probabilities (when a row omits a head) are made-up baselines from x-algo-scorer, not from X.",
            "Sample input shipped with this repo is example data, not real traffic.",
        ],
        "stages": stages,
        "stage_citations": STAGES,
        "filters": filter_rows,
        "heads_scored": _head_contributions(scored),
        "heads_exported": _head_contributions(exported),
        "score_buckets": buckets,
        "authors": _author_source_table(by_stage, "author"),
        "sources": _author_source_table(by_stage, "source"),
        "top": top_rows,
        "exported_ids": [r.get("id") for r in exported],
        "scored_ids": [r.get("id") for r in scored],
    }
    return counts
