from pathlib import Path

from x_algo_export_counter.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cli_run_and_diff(tmp_path: Path, capsys):
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    sample = ROOT / "examples" / "sample_candidates.jsonl"
    assert main(["run", str(sample), "--out", str(out_a), "--top-n", "5"]) == 0
    printed = capsys.readouterr().out
    assert "Exported (organic posts remaining" not in printed or "exported" in printed.lower()
    assert "ex-01" in (out_a / "summary.md").read_text() or "thunder" in (out_a / "summary.md").read_text()
    assert main(["run", str(sample), "--out", str(out_b), "--top-n", "8"]) == 0
    diff_dir = tmp_path / "diff"
    assert main(["diff", str(out_a / "counts.json"), str(out_b / "counts.json"), "--out", str(diff_dir)]) == 0
    assert (diff_dir / "diff.md").is_file()
    body = (diff_dir / "diff.md").read_text()
    assert "Stages" in body


def test_cli_prescored(tmp_path: Path):
    out = tmp_path / "pre"
    sample = ROOT / "examples" / "sample_prescored.csv"
    assert main(["run", str(sample), "--out", str(out), "--pre-scored"]) == 0
    summary = (out / "summary.md").read_text()
    assert "exported" in summary.lower()
    assert "age_filter" in summary
