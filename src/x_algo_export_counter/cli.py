"""CLI: count a scored batch, or diff two count exports.

Usage:
  x-algo-export-counter run input.jsonl --out counts/
  x-algo-export-counter run input.jsonl --out counts/ --top-n 10 --config weights.yml
  x-algo-export-counter run input.jsonl --out counts/ --pre-scored
  x-algo-export-counter diff a.json b.json
  x-algo-export-counter diff a.json b.json --out counts/diff
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from x_algo_export_counter.counts import build_counts
from x_algo_export_counter.diff import diff_counts, load_counts, render_diff, write_diff
from x_algo_export_counter.export import render_summary, write_counts
from x_algo_export_counter.loaders import load_records
from x_algo_export_counter.pipeline import run_pipeline
from x_algo_export_counter.scorer import DEFAULT_CONFIG_PATH, load_config


def _cmd_run(args: argparse.Namespace) -> int:
    records = load_records(args.input)
    config = load_config(args.config)
    result = run_pipeline(
        records,
        config,
        pre_scored=args.pre_scored,
        top_n=args.top_n,
    )
    counts = build_counts(result)
    if args.out:
        write_counts(counts, args.out)
        print(f"Wrote counts to {Path(args.out).resolve()}", file=sys.stderr)
    print(render_summary(counts))
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    left = load_counts(args.a)
    right = load_counts(args.b)
    diff = diff_counts(left, right)
    if args.out:
        write_diff(diff, args.out)
        print(f"Wrote diff to {Path(args.out).resolve()}", file=sys.stderr)
    print(render_diff(diff))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="x-algo-export-counter",
        description=(
            "Count results from a batch of X-algorithm scores and export the "
            "tallies. Offline toy; not a predictor."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="score (or accept pre-scored rows) and export counts")
    run.add_argument("input", help="JSON, JSONL, or CSV batch (candidates or pre-scored rows)")
    run.add_argument("--out", required=True, help="output directory for CSV, JSON, and summary.md")
    run.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="weight YAML in the x-algo-scorer schema (default: vendored public weights)",
    )
    run.add_argument(
        "--pre-scored",
        action="store_true",
        help="treat rows as already scored (require final_score; do not re-run the toy scorer)",
    )
    run.add_argument(
        "--top-n",
        type=int,
        default=None,
        help=(
            "simulate TopKScoreSelector by keeping the top K scored rows before "
            "post-selection filters. Omitted means no cutoff (K is request-dependent upstream)."
        ),
    )
    run.set_defaults(func=_cmd_run)

    diff = sub.add_parser("diff", help="compare two counts.json exports")
    diff.add_argument("a", help="counts JSON from run A (for example an older weight set)")
    diff.add_argument("b", help="counts JSON from run B")
    diff.add_argument(
        "--out",
        help="optional directory, or a .md / .json file, for the diff",
    )
    diff.set_defaults(func=_cmd_diff)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
