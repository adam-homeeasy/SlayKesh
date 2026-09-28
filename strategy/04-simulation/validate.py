#!/usr/bin/env python3
"""
Validates strategy/04-simulation/inputs/direction-*.json files against SCHEMA.md.

Checks:
  - required top-level keys present
  - all monthly arrays (min/opt) have exactly 6 entries
  - all [low, typical, high] triples are numeric and ordered low <= typical <= high
  - repeat_prob_by_months_since_first has 6 rows, row 0 == [0, 0, 0]
  - values that are probabilities/shares (cod_share, rto_rate_on_cod, gross_margin_pct,
    repeat probabilities, subscription share, affiliate pct, attributed revenue share)
    fall within [0, 1]

Usage:
    python3 validate.py                       # validates every inputs/direction-*.json
    python3 validate.py path/to/file.json ...  # validates specific files
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MONTHS = 6


class Issue(str):
    """A single validation error message."""


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check_len6(path_label: str, field_label: str, arr, errors: list[str]) -> None:
    if not isinstance(arr, list) or len(arr) != MONTHS:
        errors.append(
            f"{path_label}: {field_label} must be an array of {MONTHS} numbers "
            f"(got {arr!r})"
        )
        return
    for i, v in enumerate(arr):
        if not _is_number(v):
            errors.append(
                f"{path_label}: {field_label}[{i}] must be numeric (got {v!r})"
            )


def check_triple(
    path_label: str,
    field_label: str,
    triple,
    errors: list[str],
    prob: bool = False,
) -> None:
    if not isinstance(triple, list) or len(triple) != 3:
        errors.append(
            f"{path_label}: {field_label} must be a [low, typical, high] array of 3 "
            f"numbers (got {triple!r})"
        )
        return
    low, typical, high = triple
    for name, v in (("low", low), ("typical", typical), ("high", high)):
        if not _is_number(v):
            errors.append(
                f"{path_label}: {field_label}.{name} must be numeric (got {v!r})"
            )
            return
    if not (low <= typical <= high):
        errors.append(
            f"{path_label}: {field_label} must satisfy low <= typical <= high "
            f"(got [{low}, {typical}, {high}])"
        )
    if prob:
        for name, v in (("low", low), ("typical", typical), ("high", high)):
            if not (0.0 <= v <= 1.0):
                errors.append(
                    f"{path_label}: {field_label}.{name} must be a probability in "
                    f"[0, 1] (got {v})"
                )


def check_scenario_pair_len6(
    path_label: str, field_label: str, obj, errors: list[str]
) -> None:
    """obj is expected to be {"min": [6 nums], "opt": [6 nums]}."""
    if not isinstance(obj, dict) or "min" not in obj or "opt" not in obj:
        errors.append(
            f"{path_label}: {field_label} must have both 'min' and 'opt' arrays "
            f"(got {obj!r})"
        )
        return
    for scen in ("min", "opt"):
        check_len6(path_label, f"{field_label}.{scen}", obj.get(scen), errors)


def validate_direction(data: dict, path_label: str) -> list[str]:
    errors: list[str] = []

    required_top = [
        "direction_id",
        "direction_name",
        "scenarios",
        "fixed_costs",
        "paid_channels",
        "organic_channels",
        "variable_costs",
        "economics",
    ]
    for key in required_top:
        if key not in data:
            errors.append(f"{path_label}: missing required top-level key '{key}'")
    if errors:
        # Without the basic keys there is nothing safe left to check.
        return errors

    scenarios = data["scenarios"]
    if not isinstance(scenarios, dict) or "min" not in scenarios or "opt" not in scenarios:
        errors.append(f"{path_label}: scenarios must define both 'min' and 'opt'")

    # fixed_costs
    for idx, fc in enumerate(data.get("fixed_costs", [])):
        label = f"{path_label}: fixed_costs[{idx}] ({fc.get('name', '?')})"
        if "monthly_inr" not in fc:
            errors.append(f"{label}: missing 'monthly_inr'")
            continue
        check_scenario_pair_len6(path_label, f"fixed_costs[{idx}].monthly_inr", fc["monthly_inr"], errors)

    # paid_channels
    for idx, pc in enumerate(data.get("paid_channels", [])):
        label = f"paid_channels[{idx}] ({pc.get('name', '?')})"
        if "monthly_spend_inr" not in pc:
            errors.append(f"{path_label}: {label}: missing 'monthly_spend_inr'")
        else:
            check_scenario_pair_len6(
                path_label, f"{label}.monthly_spend_inr", pc["monthly_spend_inr"], errors
            )
        if "cac_inr" not in pc:
            errors.append(f"{path_label}: {label}: missing 'cac_inr'")
        else:
            check_triple(path_label, f"{label}.cac_inr", pc["cac_inr"], errors)
        if "cac_improvement_per_month_pct" not in pc:
            errors.append(f"{path_label}: {label}: missing 'cac_improvement_per_month_pct'")
        else:
            check_triple(
                path_label,
                f"{label}.cac_improvement_per_month_pct",
                pc["cac_improvement_per_month_pct"],
                errors,
            )
        if "diminishing_returns_k" not in pc or not _is_number(pc["diminishing_returns_k"]):
            errors.append(f"{path_label}: {label}: 'diminishing_returns_k' must be numeric")
        elif pc["diminishing_returns_k"] < 0:
            errors.append(f"{path_label}: {label}: 'diminishing_returns_k' must be >= 0")

    # organic_channels
    for idx, oc in enumerate(data.get("organic_channels", [])):
        label = f"organic_channels[{idx}] ({oc.get('name', '?')})"
        ncpm = oc.get("new_customers_per_month")
        if not isinstance(ncpm, dict) or "min" not in ncpm or "opt" not in ncpm:
            errors.append(
                f"{path_label}: {label}: 'new_customers_per_month' must have both "
                f"'min' and 'opt' objects"
            )
            continue
        for scen in ("min", "opt"):
            block = ncpm.get(scen)
            if not isinstance(block, dict) or not all(k in block for k in ("low", "typical", "high")):
                errors.append(
                    f"{path_label}: {label}.new_customers_per_month.{scen} must have "
                    f"'low', 'typical', 'high' arrays"
                )
                continue
            for k in ("low", "typical", "high"):
                check_len6(
                    path_label,
                    f"{label}.new_customers_per_month.{scen}.{k}",
                    block[k],
                    errors,
                )
            # per-month ordering low <= typical <= high
            if all(
                isinstance(block[k], list) and len(block[k]) == MONTHS
                for k in ("low", "typical", "high")
            ):
                for m in range(MONTHS):
                    lo, typ, hi = block["low"][m], block["typical"][m], block["high"][m]
                    if _is_number(lo) and _is_number(typ) and _is_number(hi):
                        if not (lo <= typ <= hi):
                            errors.append(
                                f"{path_label}: {label}.new_customers_per_month.{scen} "
                                f"month {m + 1}: low <= typical <= high violated "
                                f"(got [{lo}, {typ}, {hi}])"
                            )

    # variable_costs
    vc = data.get("variable_costs", {})
    vc_fields_prob = [
        "affiliate_commission_pct_of_attributed_revenue",
        "attributed_revenue_share_for_commission",
    ]
    vc_fields_plain = [
        "whatsapp_marketing_msgs_per_customer_per_month",
        "whatsapp_msg_cost_inr",
    ]
    for f in vc_fields_prob + vc_fields_plain:
        if f not in vc:
            errors.append(f"{path_label}: variable_costs: missing '{f}'")
        else:
            check_triple(
                path_label, f"variable_costs.{f}", vc[f], errors, prob=(f in vc_fields_prob)
            )

    # economics
    ec = data.get("economics", {})
    ec_fields_plain = [
        "aov_first_inr",
        "aov_repeat_inr",
        "fulfilment_cost_per_order_inr",
    ]
    ec_fields_prob = [
        "gross_margin_pct",
        "cod_share",
        "rto_rate_on_cod",
        "subscription_share_of_repeaters",
    ]
    ec_fields_other = ["subscription_repeat_multiplier"]
    for f in ec_fields_plain + ec_fields_prob + ec_fields_other:
        if f not in ec:
            errors.append(f"{path_label}: economics: missing '{f}'")
        else:
            check_triple(
                path_label, f"economics.{f}", ec[f], errors, prob=(f in ec_fields_prob)
            )

    rp = ec.get("repeat_prob_by_months_since_first")
    if not isinstance(rp, list) or len(rp) != MONTHS:
        errors.append(
            f"{path_label}: economics.repeat_prob_by_months_since_first must have "
            f"{MONTHS} rows (one per months-since-first, i=0..5)"
        )
    else:
        for i, row in enumerate(rp):
            check_triple(
                path_label,
                f"economics.repeat_prob_by_months_since_first[{i}]",
                row,
                errors,
                prob=True,
            )
        if isinstance(rp[0], list) and rp[0] != [0, 0, 0] and rp[0] != [0.0, 0.0, 0.0]:
            errors.append(
                f"{path_label}: economics.repeat_prob_by_months_since_first[0] "
                f"(the acquisition month) must be [0, 0, 0] (got {rp[0]!r})"
            )

    return errors


def validate_file(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path.name}: invalid JSON ({e})"]
    return validate_direction(data, path.name)


def main(argv: list[str]) -> int:
    if argv:
        files = [Path(a) for a in argv]
    else:
        files = sorted(Path(p) for p in glob.glob(str(BASE_DIR / "inputs" / "direction-*.json")))

    if not files:
        print("No input files found (inputs/direction-*.json).")
        return 0

    all_errors: list[str] = []
    for f in files:
        if not f.exists():
            all_errors.append(f"{f}: file not found")
            continue
        errs = validate_file(f)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"OK   {f.name}")

    if all_errors:
        print(f"\n{len(all_errors)} validation error(s):")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print(f"\nAll {len(files)} file(s) valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
