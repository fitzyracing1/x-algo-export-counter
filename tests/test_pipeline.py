from pathlib import Path

from x_algo_export_counter.citations import PRE_SCORING_FILTERS, POST_SELECTION_FILTERS
from x_algo_export_counter.loaders import load_records
from x_algo_export_counter.pipeline import run_pipeline
from x_algo_export_counter.scorer import load_config

ROOT = Path(__file__).resolve().parents[1]


def test_example_batch_stage_counts():
    records = load_records(ROOT / "examples" / "sample_candidates.jsonl")
    result = run_pipeline(records, load_config(), top_n=5)
    # Six pre-scoring drops in the example file: age, self, blocked, muted,
    # previously_seen, ineligible_subscription, duplicate = 7 actually.
    reasons = sorted(r["dropped_by"] for r in result["pre_dropped"])
    assert reasons == [
        "age_filter",
        "author_socialgraph_filter",
        "drop_duplicates_filter",
        "ineligible_subscription_filter",
        "previously_seen_posts_filter",
        "self_tweet_filter",
        "viewer_muted_keyword_filter",
    ]
    assert len(result["candidates"]) == 16
    assert len(result["pre_dropped"]) == 7
    assert len(result["scored"]) == 9
    assert len(result["selected"]) == 5
    assert len(result["not_selected"]) == 4
    # ex-15 has visibility_drop; it is only dropped if it made the top 5.
    post_ids = {r["id"] for r in result["post_dropped"]}
    exported_ids = {r["id"] for r in result["exported"]}
    assert "ex-09" not in exported_ids  # age filtered before scoring
    if "ex-15" in {r["id"] for r in result["selected"]}:
        assert "ex-15" in post_ids
        assert "ex-15" not in exported_ids
    for row in result["pre_dropped"]:
        assert row["known_filter"] is True
        assert row["dropped_by"] in PRE_SCORING_FILTERS


def test_unknown_filter_reason_is_labeled():
    records = [{"id": "x", "text": "hi", "filter_reason": "not_a_real_filter"}]
    result = run_pipeline(records, load_config())
    assert len(result["pre_dropped"]) == 1
    assert result["pre_dropped"][0]["known_filter"] is False
    assert "not in the cited" in result["pre_dropped"][0]["dropped_citation"]


def test_vf_filter_is_post_selection():
    records = [
        {"id": "keep", "text": "a", "predictions": {"favorite": 0.9, "report": 0.0, "not_interested": 0.0, "not_dwelled": 0.0}},
        {"id": "drop", "text": "b", "visibility_drop": True, "predictions": {"favorite": 0.8, "report": 0.0, "not_interested": 0.0, "not_dwelled": 0.0}},
    ]
    result = run_pipeline(records, load_config())
    assert {r["id"] for r in result["scored"]} == {"keep", "drop"}
    assert result["post_dropped"][0]["dropped_by"] == "vf_filter"
    assert result["post_dropped"][0]["dropped_by"] in POST_SELECTION_FILTERS
    assert [r["id"] for r in result["exported"]] == ["keep"]


def test_pre_scored_skips_toy_scorer():
    records = [
        {"id": "a", "author": "ann", "source": "thunder", "final_score": 0.2, "weighted_sum": 0.19, "terms": {"reply": 0.1}},
        {"id": "b", "author": "bob", "source": "phoenix", "final_score": 0.1, "terms": {"favorite": 0.05}},
    ]
    result = run_pipeline(records, load_config(), pre_scored=True, top_n=1)
    assert result["exported"][0]["id"] == "a"
    assert result["exported"][0]["final_score"] == 0.2
    assert result["exported"][0]["score_mode"] == "pre_scored"
    assert result["not_selected"][0]["id"] == "b"
