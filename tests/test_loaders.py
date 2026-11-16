import json
from pathlib import Path

import pytest

from x_algo_export_counter.loaders import load_records

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "sample_candidates.jsonl"


def test_jsonl_skips_comments_and_loads_examples():
    rows = load_records(EXAMPLE)
    assert len(rows) == 16
    assert rows[0]["id"] == "ex-01"
    assert rows[0]["source"] == "thunder"
    assert rows[0]["predictions"]["favorite"] == 0.03


def test_json_list(tmp_path: Path):
    path = tmp_path / "batch.json"
    path.write_text(json.dumps([{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]))
    rows = load_records(path)
    assert [r["id"] for r in rows] == ["a", "b"]


def test_csv_pred_prefix(tmp_path: Path):
    path = tmp_path / "batch.csv"
    path.write_text("id,author,source,pred_favorite,pred_reply,in_network,text\n1,ann,thunder,0.02,0.001,true,hello\n")
    rows = load_records(path)
    assert rows[0]["predictions"]["favorite"] == 0.02
    assert rows[0]["flags"]["in_network"] is True


def test_prescored_csv_example():
    rows = load_records(ROOT / "examples" / "sample_prescored.csv")
    assert len(rows) == 4
    assert rows[0]["final_score"] == 0.08 or float(rows[0]["final_score"]) == 0.08
    assert rows[2]["filter_reason"] == "age_filter"


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_records("/no/such/file.jsonl")
