# Example data

Every file in this folder is **example data**, not real X traffic and not
model output from X. The posts, authors, probabilities, and filter flags are
made up so the CLI has something to count.

- `sample_candidates.jsonl` — candidates with guessed probabilities in the
  [x-algo-scorer](https://github.com/fitzyracing1/x-algo-scorer) schema, plus
  source and filter fields named after `home-mixer/sources/` and
  `home-mixer/filters/` in [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm).
- `sample_prescored.csv` — already-scored rows (and one pre-scoring drop) for
  the `--pre-scored` path.
