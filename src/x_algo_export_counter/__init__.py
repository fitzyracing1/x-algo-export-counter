"""Count and export results from a batch of X-algorithm scores.

This is not a predictor. It tallies a local batch against the public
weighted-sum formula and the published For You stages. See the README.
"""

from x_algo_export_counter.counts import build_counts
from x_algo_export_counter.diff import diff_counts
from x_algo_export_counter.pipeline import run_pipeline

__all__ = ["build_counts", "diff_counts", "run_pipeline"]
__version__ = "0.1.0"
