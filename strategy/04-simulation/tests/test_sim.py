"""Sanity tests for sim.py. Run with:  python3 -m pytest tests/ -v
(or python3 tests/test_sim.py, which runs them without pytest)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import sim  # noqa: E402

N = 500  # small run count for fast, deterministic-enough tests


def minimal_direction() -> dict:
    """An all-zeros direction: no paid spend, no organic, no repeats, no costs."""
    return {
        "direction_id": 99,
        "direction_name": "Test Direction",
        "scenarios": {
            "min": {"label": "min", "notes": ""},
            "opt": {"label": "opt", "notes": ""},
        },
        "fixed_costs": [],
        "paid_channels": [],
        "organic_channels": [],
        "variable_costs": {
            "affiliate_commission_pct_of_attributed_revenue": [0, 0, 0],
            "attributed_revenue_share_for_commission": [0, 0, 0],
            "whatsapp_marketing_msgs_per_customer_per_month": [0, 0, 0],
            "whatsapp_msg_cost_inr": [0, 0, 0],
        },
        "economics": {
            "aov_first_inr": [1000, 1000, 1000],
            "aov_repeat_inr": [1000, 1000, 1000],
            "gross_margin_pct": [0.5, 0.5, 0.5],
            "fulfilment_cost_per_order_inr": [0, 0, 0],
            "cod_share": [0, 0, 0],
            "rto_rate_on_cod": [0, 0, 0],
            "repeat_prob_by_months_since_first": [[0, 0, 0] for _ in range(6)],
            "subscription_share_of_repeaters": [0, 0, 0],
            "subscription_repeat_multiplier": [1, 1, 1],
        },
    }


def load_example() -> dict:
    return json.loads((BASE_DIR / "inputs" / "example.json").read_text())


def test_zero_spend_zero_organic_gives_zero_revenue():
    direction = minimal_direction()
    rng = np.random.default_rng(1)
    res = sim.run_scenario(direction, "min", N, rng)
    assert np.allclose(res["new_customers_m"], 0.0)
    assert np.allclose(res["net_revenue_m"], 0.0)
    assert np.allclose(res["contribution_m"], 0.0)


def test_doubling_paid_spend_with_k_zero_doubles_paid_new_customers():
    direction = minimal_direction()
    direction["paid_channels"] = [
        {
            "name": "Test channel",
            "monthly_spend_inr": {
                "min": [1000, 1000, 1000, 1000, 1000, 1000],
                "opt": [2000, 2000, 2000, 2000, 2000, 2000],
            },
            "cac_inr": [500, 500, 500],  # constant -> no randomness
            "cac_improvement_per_month_pct": [0, 0, 0],  # no improvement -> no randomness
            "diminishing_returns_k": 0.0,
        }
    ]
    rng = np.random.default_rng(2)
    res_min = sim.run_scenario(direction, "min", N, rng)
    res_opt = sim.run_scenario(direction, "opt", N, rng)
    assert np.allclose(res_opt["new_customers_m"], 2.0 * res_min["new_customers_m"])


def test_repeat_orders_never_occur_in_acquisition_month():
    direction = load_example()
    rng = np.random.default_rng(3)
    for scen in ("min", "opt"):
        res = sim.run_scenario(direction, scen, N, rng)
        assert np.allclose(res["repeat_orders_m"][:, 0], 0.0), (
            f"scenario={scen}: month-1 (acquisition month) repeat orders must be zero"
        )


def test_roi_formula_matches_schema():
    direction = load_example()
    rng = np.random.default_rng(4)
    res = sim.run_scenario(direction, "opt", N, rng)

    spend_3m = res["cumulative_spend"][2]
    expected_roi_3m = (res["cumulative_contribution"][:, 2] - spend_3m) / spend_3m
    assert np.allclose(res["roi_3m"], expected_roi_3m, equal_nan=True)

    spend_6m = res["cumulative_spend"][5]
    expected_roi_6m = (res["cumulative_contribution"][:, 5] - spend_6m) / spend_6m
    assert np.allclose(res["roi_6m"], expected_roi_6m, equal_nan=True)


def _run_all():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return failed


if __name__ == "__main__":
    raise SystemExit(1 if _run_all() else 0)
