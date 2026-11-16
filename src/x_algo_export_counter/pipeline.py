"""Walk a batch through the cited For You stages and score or accept pre-scored rows."""

from __future__ import annotations

from x_algo_export_counter.citations import (
    FIELD_POST_SELECTION_RULES,
    FIELD_PRE_SCORING_RULES,
    POST_SELECTION_FILTERS,
    PRE_SCORING_FILTERS,
    UNAPPLIED_SCORE_ADJUSTMENTS,
    classify_filter,
    filter_citation,
)
from x_algo_export_counter.scorer import load_config, score_post


def _reason_from_record(record: dict) -> str | None:
    reason = record.get("filter_reason") or record.get("filtered_out_by")
    if reason is None or reason == "":
        return None
    return str(reason).strip()


def pre_scoring_reason(record: dict) -> str | None:
    """Return a cited pre-scoring filter name, or a raw unknown reason."""
    explicit = _reason_from_record(record)
    if explicit:
        kind = classify_filter(explicit)
        if kind == "post_selection":
            return None
        return explicit
    for name, rule in FIELD_PRE_SCORING_RULES:
        if rule(record):
            return name
    return None


def post_selection_reason(record: dict) -> str | None:
    explicit = _reason_from_record(record)
    if explicit and classify_filter(explicit) == "post_selection":
        return explicit
    # An explicit pre-scoring reason should already have dropped the row.
    for name, rule in FIELD_POST_SELECTION_RULES:
        if rule(record):
            return name
    return None


def _is_pre_scored(record: dict, force: bool) -> bool:
    if force:
        return True
    if "final_score" in record or "weighted_sum" in record:
        return True
    return False


def score_record(record: dict, config: dict, pre_scored: bool) -> dict:
    """Attach score fields. Pre-scored rows keep the provided numbers."""
    out = dict(record)
    if _is_pre_scored(record, pre_scored):
        if "final_score" not in out:
            raise ValueError(
                f"record {out.get('id')!r} is marked pre-scored but has no final_score"
            )
        out["final_score"] = float(out["final_score"])
        out["weighted_sum"] = float(out["weighted_sum"]) if "weighted_sum" in out else out["final_score"]
        out["terms"] = {k: float(v) for k, v in (out.get("terms") or {}).items()}
        out["defaulted_heads"] = list(out.get("defaulted_heads") or [])
        out["score_mode"] = "pre_scored"
        return out

    result = score_post(record, config)
    out["final_score"] = result.final_score
    out["weighted_sum"] = result.weighted_sum
    out["terms"] = dict(result.terms)
    out["predictions"] = dict(result.predictions)
    out["effective_weights"] = dict(result.effective_weights)
    out["defaulted_heads"] = list(result.defaulted_heads)
    out["flags"] = dict(result.flags)
    out["score_mode"] = "scored"
    if not out.get("text"):
        out["text"] = result.text
    return out


def run_pipeline(
    records: list[dict],
    config: dict | None = None,
    *,
    pre_scored: bool = False,
    top_n: int | None = None,
    config_path: str | None = None,
) -> dict:
    """Run the cited stages. Returns a structured result for counting/export."""
    if config is None:
        config = load_config(config_path) if config_path else load_config()

    candidates = list(records)
    pre_dropped: list[dict] = []
    to_score: list[dict] = []
    for rec in candidates:
        reason = pre_scoring_reason(rec)
        if reason:
            dropped = dict(rec)
            dropped["dropped_by"] = reason
            dropped["dropped_stage"] = "pre_scoring"
            dropped["dropped_citation"] = filter_citation(reason)
            dropped["known_filter"] = reason in PRE_SCORING_FILTERS
            pre_dropped.append(dropped)
        else:
            to_score.append(rec)

    scored: list[dict] = []
    for rec in to_score:
        scored.append(score_record(rec, config, pre_scored=pre_scored))
    scored.sort(key=lambda r: r["final_score"], reverse=True)
    for i, rec in enumerate(scored, start=1):
        rec["rank"] = i

    if top_n is None:
        selected = list(scored)
        not_selected: list[dict] = []
        top_n_applied = False
    else:
        if top_n < 0:
            raise ValueError("--top-n must be >= 0")
        selected = scored[:top_n]
        not_selected = scored[top_n:]
        for rec in not_selected:
            rec = rec  # already in scored
        top_n_applied = True

    post_dropped: list[dict] = []
    exported: list[dict] = []
    for rec in selected:
        reason = post_selection_reason(rec)
        if reason:
            dropped = dict(rec)
            dropped["dropped_by"] = reason
            dropped["dropped_stage"] = "post_selection"
            dropped["dropped_citation"] = filter_citation(reason)
            dropped["known_filter"] = reason in POST_SELECTION_FILTERS
            post_dropped.append(dropped)
        else:
            exported.append(dict(rec))

    return {
        "config": config,
        "candidates": candidates,
        "pre_dropped": pre_dropped,
        "scored": scored,
        "selected": selected,
        "not_selected": not_selected,
        "post_dropped": post_dropped,
        "exported": exported,
        "top_n": top_n,
        "top_n_applied": top_n_applied,
        "unapplied": list(UNAPPLIED_SCORE_ADJUSTMENTS),
        "pre_scored": pre_scored,
    }
