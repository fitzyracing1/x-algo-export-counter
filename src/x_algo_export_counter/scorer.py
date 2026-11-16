"""Vendored copy of the weighted-sum value model from fitzyracing1/x-algo-scorer.

Credit: scoring math and default guesses are taken from
https://github.com/fitzyracing1/x-algo-scorer/blob/e1437c75536435ca55b3047ddcc8299cc68e8893/xscore/scorer.py
and the weight YAML at that same commit (config/x-algorithm.yml), which itself
cites xai-org/x-algorithm @ 30647a85a20cbdd114169beb9973680c4dc4f401.

The math mirrors xai-value-model/scoring.rs:

    weighted = sum(prediction[head] * effective_weight[head])
    final    = offset_score(weighted)

This is a toy for exploring public weights. It is not a predictor: the real
ranker multiplies these weights by per-viewer model outputs nobody outside X
has. Default predictions below are made-up baselines from x-algo-scorer, not
from X.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from x_algo_export_counter.citations import SCORER_COMMIT, SCORER_REPO

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PACKAGE_DIR / "data" / "x-algorithm.yml"

PROBABILITY_HEADS = [
    "favorite",
    "reply",
    "retweet",
    "photo_expand",
    "video_open",
    "click",
    "open_link",
    "profile_click",
    "vqv",
    "share",
    "share_via_dm",
    "share_via_copy_link",
    "dwell",
    "quote",
    "quoted_click",
    "quoted_vqv",
    "follow_author",
    "post_unexplored",
    "post_video",
    "grok_analyze",
    "not_interested",
    "block_author",
    "mute_author",
    "report",
    "not_dwelled",
]

CONTINUOUS_HEADS = {
    "cont_dwell_time": "expected dwell seconds",
    "cont_click_dwell_time": "expected post-click dwell seconds",
}

ALL_HEADS = PROBABILITY_HEADS + list(CONTINUOUS_HEADS)

# Made-up ballpark baseline guesses copied from x-algo-scorer. NOT from X.
DEFAULT_PREDICTIONS = {
    "favorite": 0.02,
    "reply": 0.002,
    "retweet": 0.004,
    "photo_expand": 0.0,
    "video_open": 0.0,
    "click": 0.01,
    "open_link": 0.0,
    "profile_click": 0.002,
    "vqv": 0.0,
    "share": 0.001,
    "share_via_dm": 0.0005,
    "share_via_copy_link": 0.0005,
    "dwell": 0.3,
    "quote": 0.0005,
    "quoted_click": 0.0,
    "quoted_vqv": 0.0,
    "follow_author": 0.0002,
    "post_unexplored": 0.0,
    "post_video": 0.0,
    "grok_analyze": 0.0005,
    "not_interested": 0.0005,
    "block_author": 0.0001,
    "mute_author": 0.0001,
    "report": 0.00005,
    "not_dwelled": 0.45,
    "cont_dwell_time": 4.0,
    "cont_click_dwell_time": 0.0,
}

DEFAULT_FLAGS = {
    "in_network": True,
    "is_mutual_follow_author": False,
    "vqv_eligible": False,
    "quoted_vqv_eligible": False,
}


@dataclass
class ScoreResult:
    text: str
    terms: dict[str, float]
    effective_weights: dict[str, float]
    predictions: dict[str, float]
    defaulted_heads: list[str]
    weighted_sum: float
    final_score: float
    flags: dict[str, bool]
    switch_notes: list[str] = field(default_factory=list)
    inert_heads: list[str] = field(default_factory=list)


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with open(path) as f:
        config = yaml.safe_load(f)
    for section in ("source", "weights", "boosts", "constants", "switches"):
        if section not in config:
            raise ValueError(f"config missing required section: {section}")
    missing = [h for h in ALL_HEADS if h not in config["weights"]]
    if missing:
        raise ValueError(f"config missing weights for heads: {missing}")
    return config


def _weight(config: dict, section: str, key: str) -> float:
    return float(config[section][key]["value"])


def effective_weights(config: dict, flags: dict) -> dict[str, float]:
    """Mirror the weight gating in xai-value-model (weights.rs + scoring.rs)."""
    w = {h: _weight(config, "weights", h) for h in ALL_HEADS}
    reply_boost = _weight(config, "boosts", "bidirectional_follow_reply_weight_boost")
    dwell_boost = _weight(config, "boosts", "bidirectional_follow_dwell_weight_boost")
    if flags["is_mutual_follow_author"]:
        if reply_boost != 0.0:
            w["reply"] += reply_boost
        if dwell_boost != 0.0:
            w["dwell"] += dwell_boost
    if not flags["vqv_eligible"]:
        w["vqv"] = 0.0
    if not flags["quoted_vqv_eligible"]:
        w["quoted_vqv"] = 0.0
    if not flags["in_network"]:
        # post_unexplored_include_out_of_network is hardcoded false upstream
        # (home-mixer/scorers/value_model.rs).
        w["post_unexplored"] = 0.0
    return w


def _negative_sum(config: dict) -> float:
    heads = ["not_interested", "block_author", "mute_author", "report", "not_dwelled"]
    return -sum(_weight(config, "weights", h) for h in heads)


def _total_sum(config: dict) -> float:
    positive_heads = [
        h
        for h in ALL_HEADS
        if h not in ("not_interested", "block_author", "mute_author", "report", "not_dwelled")
    ]
    positive = sum(_weight(config, "weights", h) for h in positive_heads)
    return positive + _negative_sum(config)


def offset_score(weighted: float, config: dict) -> float:
    """Mirror offset_score() in xai-value-model/scoring.rs."""
    offset = _weight(config, "constants", "negative_scores_offset")
    total = _total_sum(config)
    if total == 0.0:
        return max(weighted, 0.0)
    if weighted < 0.0:
        return (weighted + _negative_sum(config)) / total * offset
    return weighted + offset


def score_post(post: dict, config: dict) -> ScoreResult:
    flags = {**DEFAULT_FLAGS, **(post.get("flags") or {})}
    unknown_flags = set(flags) - set(DEFAULT_FLAGS)
    if unknown_flags:
        raise ValueError(f"unknown flags: {sorted(unknown_flags)}")

    user_preds = post.get("predictions") or {}
    unknown_preds = set(user_preds) - set(ALL_HEADS)
    if unknown_preds:
        raise ValueError(f"unknown prediction heads: {sorted(unknown_preds)}")

    predictions = {}
    defaulted = []
    for head in ALL_HEADS:
        if head in user_preds:
            predictions[head] = float(user_preds[head])
        else:
            predictions[head] = DEFAULT_PREDICTIONS[head]
            defaulted.append(head)
    for head in PROBABILITY_HEADS:
        p = predictions[head]
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"prediction for '{head}' must be in [0, 1], got {p}")

    weights = effective_weights(config, flags)
    terms = {h: predictions[h] * weights[h] for h in ALL_HEADS}
    weighted_sum = sum(terms.values())
    final = offset_score(weighted_sum, config)
    inert = [h for h in ALL_HEADS if weights[h] == 0.0]

    return ScoreResult(
        text=str(post.get("text") or ""),
        terms=terms,
        effective_weights=weights,
        predictions=predictions,
        defaulted_heads=defaulted,
        weighted_sum=weighted_sum,
        final_score=final,
        flags=flags,
        switch_notes=[],
        inert_heads=inert,
    )


def credit_line(config: dict) -> str:
    src = config["source"]
    return (
        f"Weights from {src['repo']} @ {src['commit'][:7]} ({src['commit_date']}); "
        f"scoring formula vendored from {SCORER_REPO} @ {SCORER_COMMIT[:7]}."
    )
