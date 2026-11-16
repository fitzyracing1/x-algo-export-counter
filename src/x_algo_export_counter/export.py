"""Write count tables as JSON, CSV, and a Markdown summary."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return "" if value is None else str(value)


def render_summary(counts: dict) -> str:
    stages = counts["stages"]
    lines = [
        "# X algorithm export counts",
        "",
        counts["credit"],
        "",
        "This is a local tally of the input batch. It is not a prediction of a live For You feed.",
        "",
        "## Stages",
        "",
        "| stage | count |",
        "|---|---:|",
        f"| candidates in | {stages['candidates_in']} |",
        f"| pre-scoring filtered out | {stages['pre_scoring_filtered']} |",
        f"| scored / ranked | {stages['scored']} |",
        f"| selected (top-K) | {stages['selected']} |",
        f"| not selected (below top-K) | {stages['not_selected_top_k']} |",
        f"| post-selection filtered out | {stages['post_selection_filtered']} |",
        f"| exported | {stages['exported']} |",
        "",
    ]
    if counts.get("top_n_applied"):
        lines.append(f"Top-K cutoff applied: `--top-n {counts['top_n']}` (simulates `TopKScoreSelector` in `home-mixer/selectors/top_k_score_selector.rs`). The public repo keeps the top K; K is request-dependent and is not hardcoded here.")
    else:
        lines.append(
            "Top-K cutoff was not applied. Pass `--top-n K` to simulate `TopKScoreSelector` (`home-mixer/selectors/top_k_score_selector.rs`). The default K is not hardcoded in this tool because the public repo treats K as request-dependent."
        )
    lines += ["", "## Filtered out by reason", ""]
    if not counts["filters"]:
        lines.append("None.")
    else:
        lines += [
            "| reason | stage | count | cited? | citation |",
            "|---|---|---:|---|---|",
        ]
        for row in counts["filters"]:
            cited = "yes" if row["known_filter"] else "no (unknown reason)"
            lines.append(
                f"| {row['reason']} | {row['stage']} | {row['count']} | {cited} | {row['citation']} |"
            )
    lines += ["", "## Engagement-head contributions (scored rows)", ""]
    if not counts["heads_scored"]:
        lines.append("No scored rows.")
    else:
        lines += [
            "| head | total contribution | mean | share of abs. total |",
            "|---|---:|---:|---:|",
        ]
        for row in counts["heads_scored"]:
            if row["total_contribution"] == 0 and row["share_of_abs_total"] == 0:
                continue
            lines.append(
                f"| {row['head']} | {_fmt(row['total_contribution'])} | {_fmt(row['mean_contribution'])} | {_fmt(row['share_of_abs_total'])} |"
            )
    lines += [
        "",
        "## Score buckets (scored rows)",
        "",
        "Bucket edges are a reporting convention of this tool, not thresholds published upstream.",
        "",
        "| bucket | count |",
        "|---|---:|",
    ]
    for row in counts["score_buckets"]:
        lines.append(f"| {row['bucket']} | {row['count']} |")
    lines += ["", "## By source", ""]
    if not counts["sources"]:
        lines.append("No source field on the input rows.")
    else:
        lines += [
            "| source | candidates | scored | exported | citation |",
            "|---|---:|---:|---:|---|",
        ]
        for row in counts["sources"]:
            known = row["name"] if row.get("known_source") else f"{row['name']} (unknown source)"
            lines.append(
                f"| {known} | {row.get('candidates_in', 0)} | {row.get('scored', 0)} | {row.get('exported', 0)} | {row.get('citation', '')} |"
            )
    lines += ["", "## By author", ""]
    if not counts["authors"]:
        lines.append("No author field on the input rows.")
    else:
        lines += [
            "| author | candidates | scored | exported |",
            "|---|---:|---:|---:|",
        ]
        for row in counts["authors"]:
            lines.append(
                f"| {row['name']} | {row.get('candidates_in', 0)} | {row.get('scored', 0)} | {row.get('exported', 0)} |"
            )
    lines += ["", "## Top exported", ""]
    if not counts["top"]:
        lines.append("None exported.")
    else:
        lines += [
            "| rank | id | author | source | final_score |",
            "|---:|---|---|---|---:|",
        ]
        for row in counts["top"]:
            lines.append(
                f"| {row['rank']} | {row['id']} | {row['author']} | {row['source']} | {_fmt(row['final_score'])} |"
            )
    lines += ["", "## Known omissions (not applied)", ""]
    for item in counts["unapplied"]:
        lines.append(f"- {item}")
    lines += ["", "## Notes", ""]
    for note in counts["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def write_counts(counts: dict, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "counts.json").write_text(
        json.dumps(counts, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    (out_dir / "summary.md").write_text(render_summary(counts), encoding="utf-8")

    stage_rows = [{"stage": key, "count": value} for key, value in counts["stages"].items()]
    _write_csv(out_dir / "stages.csv", stage_rows, ["stage", "count"])
    _write_csv(
        out_dir / "filters.csv",
        counts["filters"],
        ["reason", "stage", "count", "known_filter", "citation"],
    )
    _write_csv(
        out_dir / "heads_scored.csv",
        counts["heads_scored"],
        ["head", "total_contribution", "mean_contribution", "share_of_abs_total"],
    )
    _write_csv(
        out_dir / "heads_exported.csv",
        counts["heads_exported"],
        ["head", "total_contribution", "mean_contribution", "share_of_abs_total"],
    )
    _write_csv(out_dir / "score_buckets.csv", counts["score_buckets"], ["bucket", "count", "lo", "hi"])
    _write_csv(
        out_dir / "sources.csv",
        counts["sources"],
        ["name", "candidates_in", "scored", "exported", "known_source", "citation"],
    )
    _write_csv(
        out_dir / "authors.csv",
        counts["authors"],
        ["name", "candidates_in", "scored", "exported"],
    )
    _write_csv(
        out_dir / "top.csv",
        counts["top"],
        ["rank", "id", "author", "source", "final_score", "weighted_sum", "text"],
    )
    return out_dir
