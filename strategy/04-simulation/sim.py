#!/usr/bin/env python3
"""
Monte Carlo growth simulation engine.

Reads every strategy/04-simulation/inputs/direction-*.json (see SCHEMA.md for the
input contract) and runs a monthly Monte Carlo over a 6-month horizon for two
budget scenarios per direction: "min" and "opt".

Outputs (written to results/):
  - summary.json  machine-readable totals (P10/P50/P90) per direction x scenario
  - summary.md    human-readable tables, both scenarios side by side
  - monthly.csv   direction, scenario, month, metric, p10, p50, p90

Usage:
    python3 sim.py [--runs N] [--seed S] [--validate]

--validate  only validate inputs/direction-*.json against the schema and exit
            (no simulation, no outputs). Equivalent to `python3 validate.py`.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    print(
        "numpy is required for sim.py but is not installed.\n"
        "Install it with:  pip install numpy",
        file=sys.stderr,
    )
    raise SystemExit(1)

from validate import validate_direction

BASE_DIR = Path(__file__).resolve().parent
INPUTS_DIR = BASE_DIR / "inputs"
RESULTS_DIR = BASE_DIR / "results"
MONTHS = 6
DEFAULT_RUNS = 5000
SCENARIOS = ("min", "opt")
MONTHLY_METRICS = ("new_customers", "repeat_orders", "revenue", "marketing_spend", "contribution")


# --------------------------------------------------------------------------
# Sampling helpers
# --------------------------------------------------------------------------

def tri_sample(rng: np.random.Generator, triple, size: int) -> np.ndarray:
    """Sample `size` draws from a triangular(low, typical, high) distribution.
    Falls back to a constant array when low == high."""
    low, mode, high = (float(x) for x in triple)
    if high - low <= 1e-12:
        return np.full(size, low, dtype=float)
    return rng.triangular(low, mode, high, size=size)


def triangular_ppf(u: np.ndarray, low: float, mode: float, high: float) -> np.ndarray:
    """Inverse CDF of a triangular(low, mode, high) distribution, vectorised over u
    (u in [0, 1)). Used to map one shared per-run percentile draw through each
    month's own (low, typical, high) so a run is internally consistent across
    months (a "good" run for a channel is good every month)."""
    low, mode, high = float(low), float(mode), float(high)
    if high - low <= 1e-12:
        return np.full_like(u, low, dtype=float)
    fc = (mode - low) / (high - low)
    left = u < fc
    x_left = low + np.sqrt(np.clip(u * (high - low) * (mode - low), 0.0, None))
    x_right = high - np.sqrt(np.clip((1.0 - u) * (high - low) * (high - mode), 0.0, None))
    return np.where(left, x_left, x_right)


# --------------------------------------------------------------------------
# Core simulation
# --------------------------------------------------------------------------

def run_scenario(direction: dict, scenario: str, n_runs: int, rng: np.random.Generator) -> dict:
    """Runs the Monte Carlo for one direction x scenario. Returns a dict of raw
    per-run arrays (numpy), used both for reporting and for unit tests."""
    N = n_runs

    # ---- paid channels: new customers per month, per run ----
    paid_new = np.zeros((N, MONTHS))
    for pc in direction.get("paid_channels", []):
        spend = np.array(pc["monthly_spend_inr"][scenario], dtype=float)  # (6,) deterministic
        cac_base = tri_sample(rng, pc["cac_inr"], N)  # (N,)
        improve_pct = tri_sample(rng, pc["cac_improvement_per_month_pct"], N) / 100.0  # (N,)
        k = float(pc.get("diminishing_returns_k", 0.0))
        for mo in range(MONTHS):
            m = mo + 1
            spend_m = spend[mo]
            cac_m = cac_base * np.power(1.0 - improve_pct, m - 1) * (1.0 + k * spend_m)
            cac_m = np.maximum(cac_m, 1e-6)
            if spend_m > 0:
                paid_new[:, mo] += spend_m / cac_m
            # spend_m == 0 -> contributes 0 new customers for this channel/month

    # ---- organic channels: new customers per month, per run (correlated via one
    #      shared percentile draw per run per channel) ----
    organic_new = np.zeros((N, MONTHS))
    for oc in direction.get("organic_channels", []):
        block = oc["new_customers_per_month"][scenario]
        u = rng.uniform(0.0, 1.0, size=N)  # one shared percentile for this channel, this run
        for mo in range(MONTHS):
            lo, typ, hi = block["low"][mo], block["typical"][mo], block["high"][mo]
            organic_new[:, mo] += triangular_ppf(u, lo, typ, hi)

    new_customers_m = paid_new + organic_new  # (N, 6)
    cumulative_new_customers = np.cumsum(new_customers_m, axis=1)

    # ---- economics: sampled once per run, applied across all 6 months ----
    econ = direction["economics"]
    aov_first = tri_sample(rng, econ["aov_first_inr"], N)
    aov_repeat = tri_sample(rng, econ["aov_repeat_inr"], N)
    gross_margin = tri_sample(rng, econ["gross_margin_pct"], N)
    fulfilment_cost = tri_sample(rng, econ["fulfilment_cost_per_order_inr"], N)
    cod_share = tri_sample(rng, econ["cod_share"], N)
    rto_rate = tri_sample(rng, econ["rto_rate_on_cod"], N)
    sub_share = tri_sample(rng, econ["subscription_share_of_repeaters"], N)
    sub_mult = tri_sample(rng, econ["subscription_repeat_multiplier"], N)

    rp_rows = econ["repeat_prob_by_months_since_first"]  # 6 rows, i = 0..5
    eff_p = {0: np.zeros(N)}
    for i in range(1, MONTHS):
        p_i = tri_sample(rng, rp_rows[i], N)
        eff_p[i] = np.clip(p_i * (1.0 + sub_share * (sub_mult - 1.0)), 0.0, 1.0)

    # ---- variable costs: sampled once per run, applied across all 6 months ----
    vc = direction["variable_costs"]
    affiliate_pct = tri_sample(rng, vc["affiliate_commission_pct_of_attributed_revenue"], N)
    attributed_share = tri_sample(rng, vc["attributed_revenue_share_for_commission"], N)
    wa_msgs = tri_sample(rng, vc["whatsapp_marketing_msgs_per_customer_per_month"], N)
    wa_msg_cost = tri_sample(rng, vc["whatsapp_msg_cost_inr"], N)

    # ---- repeat orders: cohort acquired in month j repeats in month j+i per eff_p[i] ----
    repeat_orders_m = np.zeros((N, MONTHS))
    for m in range(1, MONTHS + 1):  # 1-indexed month
        for j in range(1, m):  # cohorts acquired before month m
            i = m - j
            if i > 5:
                continue
            repeat_orders_m[:, m - 1] += new_customers_m[:, j - 1] * eff_p[i]

    orders_m = new_customers_m + repeat_orders_m

    # ---- revenue, RTO, contribution ----
    gross_revenue_m = new_customers_m * aov_first[:, None] + repeat_orders_m * aov_repeat[:, None]
    rto_loss_m = gross_revenue_m * cod_share[:, None] * rto_rate[:, None]
    net_revenue_m = gross_revenue_m - rto_loss_m

    fulfilment_cost_m = orders_m * fulfilment_cost[:, None]  # charged even on RTO orders
    wa_cost_m = cumulative_new_customers * wa_msgs[:, None] * wa_msg_cost[:, None]
    affiliate_commission_m = net_revenue_m * attributed_share[:, None] * affiliate_pct[:, None]

    contribution_m = (
        net_revenue_m * gross_margin[:, None] - fulfilment_cost_m - wa_cost_m - affiliate_commission_m
    )

    # ---- marketing spend (deterministic budget input, same across all runs) ----
    fixed_total = np.zeros(MONTHS)
    for fc in direction.get("fixed_costs", []):
        fixed_total += np.array(fc["monthly_inr"][scenario], dtype=float)
    paid_spend_total = np.zeros(MONTHS)
    for pc in direction.get("paid_channels", []):
        paid_spend_total += np.array(pc["monthly_spend_inr"][scenario], dtype=float)
    marketing_spend_m = fixed_total + paid_spend_total  # (6,)

    cumulative_contribution = np.cumsum(contribution_m, axis=1)
    cumulative_spend = np.cumsum(marketing_spend_m)  # (6,)
    cumulative_revenue = np.cumsum(net_revenue_m, axis=1)

    # ---- ROI, blended CAC at 3m / 6m ----
    def roi_at(k):  # k = 3 or 6 (months)
        spend_k = cumulative_spend[k - 1]
        if spend_k <= 0:
            return np.full(N, np.nan)
        return (cumulative_contribution[:, k - 1] - spend_k) / spend_k

    def blended_cac_at(k):
        spend_k = cumulative_spend[k - 1]
        cust_k = cumulative_new_customers[:, k - 1]
        return np.where(cust_k > 0, spend_k / np.maximum(cust_k, 1e-9), np.nan)

    roi_3m = roi_at(3)
    roi_6m = roi_at(6)
    cac_3m = blended_cac_at(3)
    cac_6m = blended_cac_at(6)

    # ---- payback month: first month cumulative contribution >= cumulative spend ----
    mask = cumulative_contribution >= cumulative_spend[None, :]
    any_true = mask.any(axis=1)
    first_true_idx = mask.argmax(axis=1)
    payback_month_run = np.where(any_true, first_true_idx + 1, MONTHS + 1)  # sentinel = "not within 6m"

    # ---- repeat rate @90d (cohorts month 1-3, i=1..3) / @180d (cohort month 1, i=1..5) ----
    def survival_rate(indices):
        surv = np.ones(N)
        for i in indices:
            surv *= (1.0 - eff_p[i])
        return 1.0 - surv

    # eff_p[i] depends only on "months since first" (i), not on which cohort month j it is,
    # so the "≥1 repeat within 90 days" probability is identical for the month-1, -2 and -3
    # cohorts -> cohort-weighted average over them collapses to this same value.
    repeat_rate_90d = survival_rate([1, 2, 3])
    repeat_rate_180d = survival_rate([1, 2, 3, 4, 5])  # month-1 cohort only

    return dict(
        new_customers_m=new_customers_m,
        repeat_orders_m=repeat_orders_m,
        net_revenue_m=net_revenue_m,
        marketing_spend_m=marketing_spend_m,
        contribution_m=contribution_m,
        cumulative_contribution=cumulative_contribution,
        cumulative_spend=cumulative_spend,
        cumulative_revenue=cumulative_revenue,
        cumulative_new_customers=cumulative_new_customers,
        roi_3m=roi_3m,
        roi_6m=roi_6m,
        cac_3m=cac_3m,
        cac_6m=cac_6m,
        payback_month_run=payback_month_run,
        repeat_rate_90d=repeat_rate_90d,
        repeat_rate_180d=repeat_rate_180d,
    )


# --------------------------------------------------------------------------
# Summary / percentile helpers
# --------------------------------------------------------------------------

def p10_50_90(arr: np.ndarray) -> dict:
    arr = np.asarray(arr, dtype=float)
    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        return {"p10": None, "p50": None, "p90": None}
    return {
        "p10": float(np.percentile(arr, 10)),
        "p50": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
    }


def payback_stats(payback_month_run: np.ndarray) -> dict:
    stats = p10_50_90(payback_month_run.astype(float))

    def label(v):
        if v is None:
            return None
        return "not within 6m" if v > MONTHS + 0.5 else round(v, 1)

    return {
        "p10": label(stats["p10"]),
        "p50": label(stats["p50"]),
        "p90": label(stats["p90"]),
        "share_within_6m": float(np.mean(payback_month_run <= MONTHS)),
    }


def summarize_scenario(direction: dict, scenario: str, res: dict) -> dict:
    scen_meta = direction.get("scenarios", {}).get(scenario, {})
    monthly = {}
    for metric, key in (
        ("new_customers", "new_customers_m"),
        ("repeat_orders", "repeat_orders_m"),
        ("revenue", "net_revenue_m"),
        ("contribution", "contribution_m"),
    ):
        arr = res[key]  # (N, 6)
        monthly[metric] = [p10_50_90(arr[:, m]) for m in range(MONTHS)]
    # marketing_spend is deterministic (no run-to-run variance)
    monthly["marketing_spend"] = [
        {"p10": v, "p50": v, "p90": v} for v in res["marketing_spend_m"].tolist()
    ]

    totals_3m = {
        "revenue": p10_50_90(res["cumulative_revenue"][:, 2]),
        "contribution": p10_50_90(res["cumulative_contribution"][:, 2]),
        "spend": {
            "p10": float(res["cumulative_spend"][2]),
            "p50": float(res["cumulative_spend"][2]),
            "p90": float(res["cumulative_spend"][2]),
        },
        "roi": p10_50_90(res["roi_3m"]),
        "blended_cac": p10_50_90(res["cac_3m"]),
    }
    totals_6m = {
        "revenue": p10_50_90(res["cumulative_revenue"][:, 5]),
        "contribution": p10_50_90(res["cumulative_contribution"][:, 5]),
        "spend": {
            "p10": float(res["cumulative_spend"][5]),
            "p50": float(res["cumulative_spend"][5]),
            "p90": float(res["cumulative_spend"][5]),
        },
        "roi": p10_50_90(res["roi_6m"]),
        "blended_cac": p10_50_90(res["cac_6m"]),
    }

    return {
        "label": scen_meta.get("label", scenario),
        "notes": scen_meta.get("notes", ""),
        "monthly": monthly,
        "totals_3m": totals_3m,
        "totals_6m": totals_6m,
        "repeat_rate_90d": p10_50_90(res["repeat_rate_90d"]),
        "repeat_rate_180d": p10_50_90(res["repeat_rate_180d"]),
        "payback_month": payback_stats(res["payback_month_run"]),
    }


# --------------------------------------------------------------------------
# Output writers
# --------------------------------------------------------------------------

def write_summary_json(all_results: list[dict], path: Path) -> None:
    path.write_text(json.dumps(all_results, indent=2))


def _fmt(v, decimals=0):
    if v is None:
        return "n/a"
    if isinstance(v, str):
        return v
    if decimals == 0:
        return f"{v:,.0f}"
    return f"{v:,.{decimals}f}"


def write_summary_md(all_results: list[dict], path: Path) -> None:
    lines = ["# Monte Carlo Growth Simulation — Summary", ""]
    for d in all_results:
        lines.append(f"## Direction {d['direction_id']}: {d['direction_name']}")
        lines.append("")
        for scen in SCENARIOS:
            s = d["scenarios"][scen]
            lines.append(f"**{scen.upper()} — {s['label']}**  ")
            if s.get("notes"):
                lines.append(f"_{s['notes']}_")
            lines.append("")

        header = (
            "| Metric | min P10 | min P50 | min P90 | opt P10 | opt P50 | opt P90 |"
        )
        sep = "|---|---|---|---|---|---|---|"
        lines.append(header)
        lines.append(sep)

        def row(label, get, decimals=0):
            vals = []
            for scen in SCENARIOS:
                st = get(d["scenarios"][scen])
                vals += [_fmt(st["p10"], decimals), _fmt(st["p50"], decimals), _fmt(st["p90"], decimals)]
            lines.append(f"| {label} | " + " | ".join(vals) + " |")

        row("Revenue @3m (INR)", lambda s: s["totals_3m"]["revenue"])
        row("Contribution @3m (INR)", lambda s: s["totals_3m"]["contribution"])
        row("Spend @3m (INR)", lambda s: s["totals_3m"]["spend"])
        row("ROI @3m", lambda s: s["totals_3m"]["roi"], decimals=2)
        row("Blended CAC @3m (INR)", lambda s: s["totals_3m"]["blended_cac"])
        row("Revenue @6m (INR)", lambda s: s["totals_6m"]["revenue"])
        row("Contribution @6m (INR)", lambda s: s["totals_6m"]["contribution"])
        row("Spend @6m (INR)", lambda s: s["totals_6m"]["spend"])
        row("ROI @6m", lambda s: s["totals_6m"]["roi"], decimals=2)
        row("Blended CAC @6m (INR)", lambda s: s["totals_6m"]["blended_cac"])
        row("Repeat rate @90d", lambda s: {k: (v if v is None else v) for k, v in s["repeat_rate_90d"].items()}, decimals=3)
        row("Repeat rate @180d", lambda s: s["repeat_rate_180d"], decimals=3)
        row("Payback month", lambda s: {"p10": s["payback_month"]["p10"], "p50": s["payback_month"]["p50"], "p90": s["payback_month"]["p90"]})

        lines.append("")
        lines.append(
            "Share of runs paying back within 6 months: "
            + ", ".join(
                f"{scen}={d['scenarios'][scen]['payback_month']['share_within_6m']:.1%}"
                for scen in SCENARIOS
            )
        )
        lines.append("")

    path.write_text("\n".join(lines) + "\n")


def write_monthly_csv(all_results: list[dict], path: Path) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["direction", "scenario", "month", "metric", "p10", "p50", "p90"])
        for d in all_results:
            for scen in SCENARIOS:
                s = d["scenarios"][scen]
                for metric in MONTHLY_METRICS:
                    for mo in range(MONTHS):
                        st = s["monthly"][metric][mo]
                        w.writerow(
                            [
                                d["direction_id"],
                                scen,
                                mo + 1,
                                metric,
                                st["p10"],
                                st["p50"],
                                st["p90"],
                            ]
                        )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def load_directions() -> list[tuple[Path, dict]]:
    files = sorted(Path(p) for p in glob.glob(str(INPUTS_DIR / "direction-*.json")))
    out = []
    for f in files:
        out.append((f, json.loads(f.read_text())))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Monte Carlo growth simulation engine")
    ap.add_argument("--runs", type=int, default=DEFAULT_RUNS, help="runs per direction x scenario (>=5000)")
    ap.add_argument("--seed", type=int, default=42, help="fixed random seed for reproducibility")
    ap.add_argument("--validate", action="store_true", help="only validate inputs and exit")
    args = ap.parse_args(argv)

    files = sorted(Path(p) for p in glob.glob(str(INPUTS_DIR / "direction-*.json")))
    if not files:
        print(f"No input files found in {INPUTS_DIR} (expected direction-*.json).")
        return 0

    # Always validate first.
    all_errors = []
    directions = []
    for f in files:
        data = json.loads(f.read_text())
        errs = validate_direction(data, f.name)
        if errs:
            all_errors.extend(errs)
        else:
            directions.append((f, data))

    if all_errors:
        print(f"{len(all_errors)} validation error(s):")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print(f"Validated {len(files)} input file(s): OK")
    if args.validate:
        return 0

    if args.runs < 5000:
        print(f"Warning: --runs={args.runs} is below the recommended minimum of 5000.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    all_results = []
    for f, direction in directions:
        print(f"Simulating {f.name} ({direction.get('direction_name', '')}) ...")
        scen_out = {}
        for scen in SCENARIOS:
            res = run_scenario(direction, scen, args.runs, rng)
            scen_out[scen] = summarize_scenario(direction, scen, res)
        all_results.append(
            {
                "direction_id": direction["direction_id"],
                "direction_name": direction["direction_name"],
                "runs": args.runs,
                "seed": args.seed,
                "scenarios": scen_out,
            }
        )

    write_summary_json(all_results, RESULTS_DIR / "summary.json")
    write_summary_md(all_results, RESULTS_DIR / "summary.md")
    write_monthly_csv(all_results, RESULTS_DIR / "monthly.csv")

    print(f"Wrote {RESULTS_DIR / 'summary.json'}")
    print(f"Wrote {RESULTS_DIR / 'summary.md'}")
    print(f"Wrote {RESULTS_DIR / 'monthly.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
