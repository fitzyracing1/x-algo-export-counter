"""Vendored scorer should match the x-algo-scorer formula on the sample post."""

from x_algo_export_counter.scorer import load_config, score_post


SAMPLE = {
    "text": "Just put my lap times from the sim into a spreadsheet and I am slower than I thought. Full data in the reply.",
    "predictions": {
        "favorite": 0.03,
        "reply": 0.004,
        "retweet": 0.005,
        "quote": 0.001,
        "share": 0.002,
        "click": 0.02,
        "dwell": 0.35,
        "cont_dwell_time": 5.0,
        "report": 0.00002,
        "not_dwelled": 0.4,
    },
    "flags": {
        "in_network": True,
        "is_mutual_follow_author": False,
        "vqv_eligible": False,
        "quoted_vqv_eligible": False,
    },
}


def test_sample_post_score_is_deterministic():
    result = score_post(SAMPLE, load_config())
    # Recomputed from the vendored weights and offset_score; pinned so weight
    # drift in the YAML fails the test the same way x-algo-scorer does.
    assert abs(result.weighted_sum - 0.071041) < 1e-6
    assert abs(result.final_score - 0.072041) < 1e-6
    assert result.terms["reply"] == 0.004 * 5.0
    assert result.terms["favorite"] == 0.03 * 0.708
    assert "vqv" in result.inert_heads  # eligibility gate, weight zeroed


def test_mutual_follow_boosts_reply_weight():
    post = {
        "text": "hi",
        "predictions": {"reply": 0.01},
        "flags": {"is_mutual_follow_author": True},
    }
    result = score_post(post, load_config())
    # base 5.0 + boost 15.0 from home-mixer/params/param.rs
    assert result.effective_weights["reply"] == 20.0
    assert result.terms["reply"] == 0.01 * 20.0
