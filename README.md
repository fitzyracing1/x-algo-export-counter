# x-algo-export-counter

Count the results a batch of posts produces under the public X For You
scoring formula, then export those counts.

You give it a JSON, JSONL, or CSV batch (candidates with guessed
probabilities, or already-scored rows). It walks the published For You
stages, tallies what got through, and writes CSV, JSON, and a Markdown
summary.

This is an offline toy. It does not call the X API, and it is not a
predictor of a live feed.

## This is not a predictor

The real ranker, documented in
[xai-org/x-algorithm](https://github.com/xai-org/x-algorithm), multiplies
public engagement-head weights by *per-viewer model-predicted
probabilities* (P(favorite), P(reply), expected dwell seconds, and so on).
Nobody outside X has those models. When this tool scores a row, it uses
your guesses or the labeled made-up defaults from
[fitzyracing1/x-algo-scorer](https://github.com/fitzyracing1/x-algo-scorer).
The number is useful for counting how weights, filters, and a top-K cutoff
move a local batch around — nothing more.

## Install

```bash
pipx install git+https://github.com/fitzyracing1/x-algo-export-counter
# or, from a checkout:
pip install -e ".[dev]"
```

## Usage

```bash
x-algo-export-counter run input.jsonl --out counts/
x-algo-export-counter run input.jsonl --out counts/ --top-n 10
x-algo-export-counter run input.jsonl --out counts/ --config my-weights.yml
x-algo-export-counter run input.csv --out counts/ --pre-scored
x-algo-export-counter diff counts-a/counts.json counts-b/counts.json
x-algo-export-counter diff counts-a/counts.json counts-b/counts.json --out counts/diff
```

`--out` on `run` is required and receives `counts.json`, `summary.md`, and
CSV tables (`stages.csv`, `filters.csv`, `heads_scored.csv`,
`heads_exported.csv`, `score_buckets.csv`, `sources.csv`, `authors.csv`,
`top.csv`).

`diff` compares two `counts.json` files, including two runs that used
different weight YAML files. It reports stage, filter, head, bucket,
author, and source deltas, plus exported-set membership changes.

## What gets counted

Stages follow the For You request path in the
[xai-org/x-algorithm README](https://github.com/xai-org/x-algorithm/blob/30647a85a20cbdd114169beb9973680c4dc4f401/README.md)
at commit `30647a85a20cbdd114169beb9973680c4dc4f401` (2026-11-14):

1. **Candidates in** — every input row, with an optional `source` named after
   `home-mixer/sources/` (Thunder is in-network; Phoenix, SimClusters, and
   popular posts are the out-of-network sources the README diagram names).
2. **Pre-scoring filters** — `home-mixer/filters/`. Rows can carry an explicit
   `filter_reason`, or fields this tool will apply when present: `age_hours > 48`
   (`age_filter`; README: "older than 48 hours"), `is_self`,
   `author_blocked` / `author_muted`, `muted_keyword`, `previously_seen`,
   `previously_served`, `duplicate`, `ineligible_subscription`.
3. **Scored / ranked** — the weighted sum and `offset_score` from
   `xai-value-model/scoring.rs`, as vendored from x-algo-scorer (which
   mirrors `home-mixer/scorers/value_model.rs`).
4. **Selected** — optional `--top-n K`, simulating
   `home-mixer/selectors/top_k_score_selector.rs` ("sort by final score, keep
   the top K"). The public repo does not publish a single default K (it is
   request-dependent), so this tool does **not** invent one. Omit `--top-n`
   and every scored row stays selected.
5. **Post-selection filters** — `vf_filter` (`visibility_drop` / `vf_drop`)
   and `dedup_conversation_filter` (`dedup_conversation`), the two filters
   the README names after Top-K.
6. **Exported** — the organic posts still standing, i.e. the posts that
   would be handed to `BlenderSelector`
   (`home-mixer/selectors/blender_selector.rs`). This tool does not invent
   ads, Who to Follow, or prompt slots.

It also counts:

- contribution totals per engagement head (favorite, reply, report, …)
- score buckets (a reporting convention of this tool, not upstream thresholds)
- per author and per source, at the candidate / scored / exported stages
- the top exported rows

A reason or source that is not in the cited file list is still counted, and
is labeled unknown.

## Weights and credit

The scoring formula and `src/x_algo_export_counter/data/x-algorithm.yml`
are a vendored copy of
[fitzyracing1/x-algo-scorer](https://github.com/fitzyracing1/x-algo-scorer)
at `e1437c75536435ca55b3047ddcc8299cc68e8893`, which itself pins every
weight to a param key and file in xai-org/x-algorithm at `30647a8`. x-algo-scorer
is not a pip package, so the copy lives here with credit rather than as a
git dependency. That repo was not modified.

Highlights, all from that upstream commit (see the YAML for the full table):

- reply `5.0`, favorite `0.708`, retweet `1.0`, share `2.118`, quote `5.0`,
  follow-author `4.0`; report `-234.0`, mute `-58.8`, not-interested
  `-53.07`, block `-31.2` (`home-mixer/params/param.rs`)
- mutual-follow reply boost `+15.0` (same file)
- `offset_score` uses `NEGATIVE_SCORES_OFFSET = 0.001`
  (`xai-value-model/weights.rs`)

`--config` accepts another YAML in the same schema so you can diff two
weight sets (for example after an upstream changelog change). This repo
does not invent a historical weight file. The public changelog of weight
and switch changes lives in the x-algorithm README "Notable Updates" and
in the notes in x-algo-scorer's YAML (for example
`VMRankerSendDppHistory` flipping false → true in commit `30647a8`).

[fitzyracing1/knobs](https://github.com/fitzyracing1/knobs) and
[knoblog](https://github.com/fitzyracing1/knoblog) document silent default
changes in general; they are not an X-algorithm changelog, and no
`XAlgoChange` symbol showed up in those repos or in other fitzyracing1
code search.

The older public snapshot at
[twitter/the-algorithm](https://github.com/twitter/the-algorithm) (2023,
Scala) is a different generation of the stack. This tool follows the
current For You path in xai-org/x-algorithm.

## What this tool does not apply

These are published stages or adjustments that are **not** run here,
because the exact inputs or coefficients were not vendored. They are
omissions, not silent zeros:

- repeated-author decay, out-of-network discount, and new-author boost in
  `home-mixer/scorers/value_model.rs`
- DPP diversity re-ordering in `vm-ranker/dpp.rs` (needs candidate
  similarities this tool does not have; `DppEnabled` is true and
  `DppMaxSelectedRank` is 150 at the pinned commit)
- Phoenix retrieval or the Phoenix probability model itself
  (`home-mixer/scorers/phoenix_scorer.rs`); you supply those probabilities
- ads, Who to Follow, and other blender slots

## Input shape

A JSONL row looks like this (every file in `examples/` is labeled example
data):

```json
{
  "id": "ex-01",
  "author": "sim_racer",
  "source": "thunder",
  "text": "…",
  "age_hours": 6,
  "predictions": {"favorite": 0.03, "reply": 0.004},
  "flags": {"in_network": true, "is_mutual_follow_author": false}
}
```

Pre-scored rows need `final_score` (and optionally `weighted_sum` and
`terms`) and are used as-is with `--pre-scored`, or automatically if
`final_score` is present. CSV columns can use `pred_favorite`,
`term_reply`, or a JSON `predictions` cell.

## Notation reserved / TBD

The shorthand `4xb -cd 1/2t -1 f c d b` was provided as an algorithm note
alongside this work. It was not found in
[x-algo-scorer](https://github.com/fitzyracing1/x-algo-scorer),
[3xb-api](https://github.com/fitzyracing1/3xb-api),
mars-crawler, knobs, knoblog, or other fitzyracing1 code under the name
`4xb` or `XAlgoChange`. This tool does not invent a meaning for it. The
notation is reserved and left TBD.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Joshua Almeida
(fitzyracing1). Not affiliated with X or xAI. Upstream values and stage
names belong to [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm).
The vendored scoring formula is credited to
[fitzyracing1/x-algo-scorer](https://github.com/fitzyracing1/x-algo-scorer).
