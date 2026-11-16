"""Cited stages, sources, and filters from the public X algorithm repos.

Every name here maps to a path in xai-org/x-algorithm at the commit pinned
in the vendored weight file (currently 30647a85a20cbdd114169beb9973680c4dc4f401,
2026-11-14), unless a note says otherwise.

The 2023 twitter/the-algorithm repo is the earlier public snapshot of the
recommendation stack (Scala). This tool follows the current For You path
documented in xai-org/x-algorithm, which is what fitzyracing1/x-algo-scorer
mirrors.
"""

from __future__ import annotations

UPSTREAM_REPO = "https://github.com/xai-org/x-algorithm"
UPSTREAM_COMMIT = "30647a85a20cbdd114169beb9973680c4dc4f401"
UPSTREAM_COMMIT_DATE = "2026-11-14"
SCORER_REPO = "https://github.com/fitzyracing1/x-algo-scorer"
SCORER_COMMIT = "e1437c75536435ca55b3047ddcc8299cc68e8893"
LEGACY_ALGO_REPO = "https://github.com/twitter/the-algorithm"

# Pipeline stages from the For You request-path diagram in README.md at the
# pinned commit (PhoenixCandidatePipeline, then ForYouCandidatePipeline).
STAGES = [
    {
        "id": "candidates_in",
        "label": "Candidates in",
        "citation": "home-mixer/sources/ and home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs",
    },
    {
        "id": "pre_scoring_filtered",
        "label": "Pre-scoring filtered out",
        "citation": "home-mixer/filters/ (README step 4, pre-scoring filters)",
    },
    {
        "id": "scored",
        "label": "Scored / ranked",
        "citation": "home-mixer/scorers/value_model.rs (RankingScorer), xai-value-model/scoring.rs, home-mixer/scorers/phoenix_scorer.rs, home-mixer/scorers/vm_ranker.rs",
    },
    {
        "id": "selected",
        "label": "Selected (Top-K)",
        "citation": "home-mixer/selectors/top_k_score_selector.rs (README step 6: sort by final score, keep the top K)",
    },
    {
        "id": "post_selection_filtered",
        "label": "Post-selection filtered out",
        "citation": "home-mixer/filters/vf_filter.rs, home-mixer/filters/dedup_conversation_filter.rs (README step 7)",
    },
    {
        "id": "exported",
        "label": "Exported (organic posts remaining for the blender / served slate)",
        "citation": "home-mixer/candidate_pipeline/for_you_candidate_pipeline.rs and home-mixer/selectors/blender_selector.rs; side_effects record served posts",
    },
]

# Candidate sources named in the README request-path diagram and/or present
# under home-mixer/sources/. Only these keys are treated as known sources.
SOURCES = {
    "thunder": {
        "network": "in-network",
        "file": "home-mixer/sources/thunder_source.rs",
        "note": "README: recent posts from accounts the viewer follows (thunder/)",
    },
    "phoenix": {
        "network": "out-of-network",
        "file": "home-mixer/sources/phoenix_source.rs",
        "note": "README: Phoenix retrieval model (phoenix/)",
    },
    "phoenix_moe": {
        "network": "out-of-network",
        "file": "home-mixer/sources/phoenix_moe_source.rs",
    },
    "phoenix_topics": {
        "network": "out-of-network",
        "file": "home-mixer/sources/phoenix_topics_source.rs",
    },
    "simclusters": {
        "network": "out-of-network",
        "file": "home-mixer/sources/simclusters_source.rs",
        "note": "README: cluster similarity (simclusters/)",
    },
    "popular_posts": {
        "network": "out-of-network",
        "file": "home-mixer/sources/popular_posts_source.rs",
        "note": "README: shared popular-posts list",
    },
    "popular_topics": {
        "network": "out-of-network",
        "file": "home-mixer/sources/popular_topics_source.rs",
    },
    "tweet_mixer": {
        "network": "out-of-network",
        "file": "home-mixer/sources/tweet_mixer_source.rs",
    },
    "cached_posts": {
        "network": "unspecified",
        "file": "home-mixer/sources/cached_posts_source.rs",
    },
    "reverse_chron_posts": {
        "network": "in-network",
        "file": "home-mixer/sources/reverse_chron_posts_source.rs",
    },
    "scored_posts": {
        "network": "unspecified",
        "file": "home-mixer/sources/scored_posts_source.rs",
    },
    "seed_candidates": {
        "network": "unspecified",
        "file": "home-mixer/sources/seed_candidates_source.rs",
    },
    "following_night_owl": {
        "network": "in-network",
        "file": "home-mixer/sources/following_night_owl_source.rs",
    },
}

# Every file in home-mixer/filters/ at the pinned commit. Classification as
# pre-scoring vs post-selection follows the README request-path diagram for
# the two filters it names in step 7; the rest default to pre-scoring, which
# is an assumption except for the README's step-4 examples (duplicates, age,
# self posts, blocks/mutes, muted keywords, already seen/served, subscriber-only).
POST_SELECTION_FILTERS = {
    "vf_filter": {
        "file": "home-mixer/filters/vf_filter.rs",
        "note": "README step 7: removes posts visibility-filtering said to drop",
    },
    "dedup_conversation_filter": {
        "file": "home-mixer/filters/dedup_conversation_filter.rs",
        "note": "README step 7: collapses branches of one conversation",
    },
}

PRE_SCORING_FILTERS = {
    "ad_adjacent_served_filter": {"file": "home-mixer/filters/ad_adjacent_served_filter.rs"},
    "age_filter": {
        "file": "home-mixer/filters/age_filter.rs",
        "note": "README step 4 lists 'older than 48 hours' among pre-scoring filters",
        "rule": "age_hours > 48",
    },
    "ancestor_video_filter": {"file": "home-mixer/filters/ancestor_video_filter.rs"},
    "ancillary_vf_filter": {"file": "home-mixer/filters/ancillary_vf_filter.rs"},
    "author_socialgraph_filter": {
        "file": "home-mixer/filters/author_socialgraph_filter.rs",
        "note": "README step 4: blocked and muted accounts",
        "rule": "author_blocked or author_muted",
    },
    "core_data_hydration_filter": {"file": "home-mixer/filters/core_data_hydration_filter.rs"},
    "drop_duplicates_filter": {
        "file": "home-mixer/filters/drop_duplicates_filter.rs",
        "note": "README step 4: duplicates across sources",
        "rule": "duplicate is true",
    },
    "fair_share_ranking_filter": {"file": "home-mixer/filters/fair_share_ranking_filter.rs"},
    "fav_holdout_filter": {"file": "home-mixer/filters/fav_holdout_filter.rs"},
    "following_retweet_deduplication_filter": {
        "file": "home-mixer/filters/following_retweet_deduplication_filter.rs",
    },
    "following_viewer_muted_keyword_filter": {
        "file": "home-mixer/filters/following_viewer_muted_keyword_filter.rs",
    },
    "ineligible_subscription_filter": {
        "file": "home-mixer/filters/ineligible_subscription_filter.rs",
        "note": "README step 4: subscriber-only posts the viewer cannot access",
        "rule": "ineligible_subscription is true",
    },
    "invalid_conversation_module_filter": {
        "file": "home-mixer/filters/invalid_conversation_module_filter.rs",
    },
    "inventory_holdout_filter": {"file": "home-mixer/filters/inventory_holdout_filter.rs"},
    "new_user_min_engagement_filter": {
        "file": "home-mixer/filters/new_user_min_engagement_filter.rs",
    },
    "new_user_soft_nsfw_filter": {"file": "home-mixer/filters/new_user_soft_nsfw_filter.rs"},
    "oon_nsfw_simclusters_filter": {"file": "home-mixer/filters/oon_nsfw_simclusters_filter.rs"},
    "oon_retweet_reply_filter": {"file": "home-mixer/filters/oon_retweet_reply_filter.rs"},
    "popular_topics_author_dedup_filter": {
        "file": "home-mixer/filters/popular_topics_author_dedup_filter.rs",
    },
    "previously_seen_posts_backup_filter": {
        "file": "home-mixer/filters/previously_seen_posts_backup_filter.rs",
    },
    "previously_seen_posts_filter": {
        "file": "home-mixer/filters/previously_seen_posts_filter.rs",
        "note": "README step 4: already seen",
        "rule": "previously_seen is true",
    },
    "previously_served_posts_filter": {
        "file": "home-mixer/filters/previously_served_posts_filter.rs",
        "note": "README step 4: already served",
        "rule": "previously_served is true",
    },
    "push_to_home_dedup_filter": {"file": "home-mixer/filters/push_to_home_dedup_filter.rs"},
    "result_size_filter": {"file": "home-mixer/filters/result_size_filter.rs"},
    "retweet_deduplication_filter": {
        "file": "home-mixer/filters/retweet_deduplication_filter.rs",
    },
    "self_reply_chain_filter": {"file": "home-mixer/filters/self_reply_chain_filter.rs"},
    "self_tweet_filter": {
        "file": "home-mixer/filters/self_tweet_filter.rs",
        "note": "README step 4: the viewer's own posts",
        "rule": "is_self is true",
    },
    "topic_ids_filter": {"file": "home-mixer/filters/topic_ids_filter.rs"},
    "video_carousel_filter": {"file": "home-mixer/filters/video_carousel_filter.rs"},
    "video_filter": {"file": "home-mixer/filters/video_filter.rs"},
    "viewer_muted_keyword_filter": {
        "file": "home-mixer/filters/viewer_muted_keyword_filter.rs",
        "note": "README step 4: muted keywords",
        "rule": "muted_keyword is true",
    },
    "zero_fav_codivert_filter": {"file": "home-mixer/filters/zero_fav_codivert_filter.rs"},
}

# Field-driven rules we will actually apply. Only rules cited above.
FIELD_PRE_SCORING_RULES = [
    ("age_filter", lambda r: _num(r, "age_hours") is not None and _num(r, "age_hours") > 48),
    ("self_tweet_filter", lambda r: _truthy(r, "is_self")),
    ("author_socialgraph_filter", lambda r: _truthy(r, "author_blocked") or _truthy(r, "author_muted")),
    ("viewer_muted_keyword_filter", lambda r: _truthy(r, "muted_keyword")),
    ("previously_seen_posts_filter", lambda r: _truthy(r, "previously_seen")),
    ("previously_served_posts_filter", lambda r: _truthy(r, "previously_served")),
    ("drop_duplicates_filter", lambda r: _truthy(r, "duplicate")),
    ("ineligible_subscription_filter", lambda r: _truthy(r, "ineligible_subscription")),
]

FIELD_POST_SELECTION_RULES = [
    ("vf_filter", lambda r: _truthy(r, "visibility_drop") or _truthy(r, "vf_drop")),
    ("dedup_conversation_filter", lambda r: _truthy(r, "dedup_conversation")),
]

ALL_FILTERS = {**PRE_SCORING_FILTERS, **POST_SELECTION_FILTERS}

# Reporting buckets for final_score. This binning is a convention of this tool,
# not a threshold published in xai-org/x-algorithm.
SCORE_BUCKETS = [
    ("< 0", None, 0.0),
    ("0 to 0.01", 0.0, 0.01),
    ("0.01 to 0.05", 0.01, 0.05),
    ("0.05 to 0.10", 0.05, 0.10),
    ("0.10 to 0.50", 0.10, 0.50),
    (">= 0.50", 0.50, None),
]

# RankingScorer also applies repeated-author decay, an out-of-network discount,
# and a new-author boost (README step 5, home-mixer/scorers/value_model.rs).
# This tool does not apply those adjustments: the exact coefficients were not
# vendored from that file. Labeled as a known omission, not an assumption that
# they are zero.
UNAPPLIED_SCORE_ADJUSTMENTS = [
    "repeated-author decay (home-mixer/scorers/value_model.rs; not vendored)",
    "out-of-network discount (home-mixer/scorers/value_model.rs; not vendored)",
    "new-author boost (home-mixer/scorers/value_model.rs; not vendored)",
    "DPP diversity re-order (vm-ranker/dpp.rs; needs candidate similarities this tool does not have)",
]


def _truthy(record: dict, key: str) -> bool:
    value = record.get(key)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _num(record: dict, key: str) -> float | None:
    value = record.get(key)
    if value is None or value == "":
        return None
    return float(value)


def classify_filter(name: str) -> str:
    if name in POST_SELECTION_FILTERS:
        return "post_selection"
    if name in PRE_SCORING_FILTERS:
        return "pre_scoring"
    return "unknown"


def filter_citation(name: str) -> str:
    info = ALL_FILTERS.get(name)
    if not info:
        return "not in the cited home-mixer/filters/ list at the pinned commit (unknown reason)"
    note = info.get("note", "")
    return f"{info['file']}" + (f" — {note}" if note else "")


def source_citation(name: str) -> str:
    info = SOURCES.get(name)
    if not info:
        return "not in the cited home-mixer/sources/ list at the pinned commit"
    note = info.get("note", "")
    return f"{info['file']} ({info['network']})" + (f" — {note}" if note else "")
