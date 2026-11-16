from pathlib import Path

from x_algo_export_counter.counts import build_counts
from x_algo_export_counter.diff import diff_counts
from x_algo_export_counter.export import render_summary, write_counts
from x_algo_export_counter.loaders import load_records
from x_algo_export_counter.pipeline import run_pipeline
from x_algo_export_counter.scorer import load_config

ROOT = Path(__file__).resolve().parents[1]


def _example_counts(top_n=5):
    records = load_records(ROOT / "examples" / "sample_candidates.jsonl")
    result = run_pipeline(records, load_config(), top_n=top_n)
    return build_counts(result)


def test_counts_tables_and_summary(tmp_path: Path):
    counts = _example_counts()
    assert counts["stages"]["candidates_in"] == 16
    assert counts["stages"]["pre_scoring_filtered"] == 7
    assert counts["stages"]["scored"] == 9
    assert sum(row["count"] for row in counts["filters"]) == 7 + counts["stages"]["post_selection_filtered"]
    thunder = next(r for r in counts["sources"] if r["name"] == "thunder")
    assert thunder["known_source"] is True
    assert "thunder_source.rs" in thunder["citation"]
    authors = {r["name"]: r for r in counts["authors"]}
    assert authors["sim_racer"]["candidates_in"] == 2
    buckets = {r["bucket"]: r["count"] for r in counts["score_buckets"]}
    assert sum(buckets.values()) == counts["stages"]["scored"]
    text = render_summary(counts)
    assert "candidates in" in text
    assert "Top-K cutoff applied" in text
    assert "xai-org/x-algorithm" in text
    out = write_counts(counts, tmp_path / "counts")
    for name in (
        "counts.json",
        "summary.md",
        "stages.csv",
        "filters.csv",
        "heads_scored.csv",
        "sources.csv",
        "authors.csv",
        "top.csv",
        "score_buckets.csv",
    ):
        assert (out / name).is_file()


def test_diff_detects_top_n_change():
    a = _example_counts(top_n=5)
    b = _example_counts(top_n=8)
    diff = diff_counts(a, b)
    selected = next(r for r in diff["stages"] if r["name"] == "selected")
    assert selected["a"] == 5
    assert selected["b"] == 8
    assert selected["delta"] == 3
    assert diff["exported_only_in_b"] or b["stages"]["exported"] >= a["stages"]["exported"]
