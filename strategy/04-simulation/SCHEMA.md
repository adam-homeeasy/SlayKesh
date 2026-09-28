# Simulation Input Schema (contract between direction agents and the sim engine)

Each strategic direction writes one file: `strategy/04-simulation/inputs/direction-<N>.json`.
The engine (`strategy/04-simulation/sim.py`) reads every file in `inputs/` and runs a monthly Monte Carlo over 6 months for two budget scenarios: `min` and `opt`.

All money is INR. Every range is `[low, typical, high]` and is sampled as a triangular distribution (low=min, typical=mode, high=max). Arrays of 6 are month 1..6.

```json
{
  "direction_id": 1,
  "direction_name": "Founder-led Scalp Truth",
  "scenarios": {
    "min": { "label": "Minimum viable budget", "notes": "what gets cut vs opt" },
    "opt": { "label": "Optimum budget",        "notes": "..." }
  },

  "fixed_costs": [
    { "name": "Freelance editor", "monthly_inr": { "min": [15000,15000,15000,15000,15000,15000], "opt": [30000,30000,30000,30000,30000,30000] } },
    { "name": "WhatsApp BSP platform", "monthly_inr": { "min": [1700,1700,1700,1700,1700,1700], "opt": [2600,2600,2600,2600,2600,2600] } }
  ],

  "paid_channels": [
    {
      "name": "Meta click-to-WhatsApp ads",
      "monthly_spend_inr": { "min": [0,10000,15000,15000,20000,20000], "opt": [20000,30000,40000,50000,60000,60000] },
      "cac_inr": [450, 700, 1100],
      "cac_improvement_per_month_pct": [0, 3, 6],
      "diminishing_returns_k": 0.000004
    }
  ],

  "organic_channels": [
    {
      "name": "Instagram organic + founder Reels",
      "new_customers_per_month": {
        "min": { "low": [5,8,12,15,18,22], "typical": [10,15,22,30,38,45], "high": [18,28,40,55,70,85] },
        "opt": { "low": [8,12,18,25,32,40], "typical": [15,25,38,52,66,80], "high": [25,42,62,85,110,135] }
      }
    }
  ],

  "variable_costs": {
    "affiliate_commission_pct_of_attributed_revenue": [0.0, 0.0, 0.0],
    "attributed_revenue_share_for_commission": [0.0, 0.0, 0.0],
    "whatsapp_marketing_msgs_per_customer_per_month": [2, 4, 6],
    "whatsapp_msg_cost_inr": [0.95, 1.02, 1.10]
  },

  "economics": {
    "aov_first_inr": [749, 950, 1200],
    "aov_repeat_inr": [749, 900, 1150],
    "gross_margin_pct": [0.62, 0.68, 0.74],
    "fulfilment_cost_per_order_inr": [80, 110, 140],
    "cod_share": [0.30, 0.40, 0.50],
    "rto_rate_on_cod": [0.05, 0.09, 0.12],
    "repeat_prob_by_months_since_first": [
      [0.00, 0.00, 0.00],
      [0.06, 0.10, 0.14],
      [0.05, 0.08, 0.12],
      [0.04, 0.07, 0.10],
      [0.03, 0.06, 0.09],
      [0.03, 0.05, 0.08]
    ],
    "subscription_share_of_repeaters": [0.0, 0.1, 0.2],
    "subscription_repeat_multiplier": [1.3, 1.6, 2.0]
  }
}
```

## Semantics

- **paid_channels**: new customers in month m = spend_m / CAC_m, where CAC_m = sampled CAC × (1 − improvement)^(m−1) × (1 + k × spend_m) (diminishing returns). k=0 disables saturation.
- **organic_channels**: new customers sampled per month from the low/typical/high arrays for that scenario (triangular per month, correlated via one shared percentile draw per run so a "good" run is good all 6 months).
- **repeat_prob_by_months_since_first[i]**: probability a customer acquired in month m places a repeat order in month m+i (i=0 is the acquisition month). Row 0 must be 0. Values are per-customer monthly probabilities; a customer can repeat more than once. Subscription share of repeaters multiplies their repeat probability.
- **Revenue** = orders × AOV, minus RTO losses (cod_share × rto_rate × revenue lost, plus fulfilment cost still incurred).
- **Contribution** = revenue × gross_margin − fulfilment − WA message costs − affiliate commissions.
- **Marketing spend** = fixed_costs + paid spend.
- **ROI** = (cumulative contribution − cumulative marketing spend) / cumulative marketing spend.
- **Repeat rate @90d / @180d** = share of month-1..3 cohorts with ≥1 repeat order within 90 / 180 days (as far as the 6-month horizon allows).

## Engine outputs (per direction × scenario, P10 / P50 / P90 over ≥5,000 runs)
Monthly: new customers, repeat orders, revenue, marketing spend, contribution. Totals at 3 and 6 months: revenue, contribution, spend, ROI, blended CAC, repeat rate @90d/@180d, payback month (first month cumulative contribution ≥ cumulative spend, or "not within 6m").
Files: `results/summary.json`, `results/summary.md`, `results/monthly.csv`.
