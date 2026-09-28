# Monte Carlo Growth Simulation Engine

Simulates 6 months of growth economics for each marketing strategy direction, under a
"min" (minimum viable budget) and "opt" (optimum budget) scenario, using Monte Carlo
sampling over the uncertain inputs (CAC, organic reach, AOV, margins, repeat rates, etc).
The exact input contract is `SCHEMA.md`; read it first if you're writing a new
`inputs/direction-N.json`.

## Setup

```
pip install numpy   # only external dependency
```

## Running

1. Drop one `inputs/direction-<N>.json` file per strategic direction (see `SCHEMA.md`
   for the format; `inputs/example.json` is a valid reference fixture — it is not
   picked up by the engine because it doesn't match `direction-*.json`).
2. Run the simulation:

```
python3 sim.py                      # 5,000 runs/scenario, seed 42
python3 sim.py --runs 20000         # more runs, still reproducible (fixed seed)
python3 sim.py --seed 7             # different fixed seed
python3 sim.py --validate           # only validate inputs/, don't simulate
```

Every run first validates all `inputs/direction-*.json` files and aborts (exit code 1,
errors printed) if any file breaks the schema. On success it writes, to `results/`:

- `summary.json` — full P10/P50/P90 stats per direction x scenario (monthly + totals)
- `summary.md` — human-readable tables, min vs opt side by side
- `monthly.csv` — `direction, scenario, month, metric, p10, p50, p90` for
  `new_customers`, `repeat_orders`, `revenue`, `marketing_spend`, `contribution`

Re-running with the same `--seed`/`--runs` reproduces byte-identical numbers.

## Validating inputs only

```
python3 validate.py                       # validates every inputs/direction-*.json
python3 validate.py inputs/some-file.json # validates specific file(s)
```

Checks array lengths (must be 6 for monthly series), that every `[low, typical, high]`
triple is ordered `low <= typical <= high`, that `repeat_prob_by_months_since_first`
row 0 (the acquisition month) is `[0, 0, 0]`, and that probability-like fields
(`gross_margin_pct`, `cod_share`, `rto_rate_on_cod`, repeat probabilities, subscription
share, affiliate commission %/share) fall in `[0, 1]`. Errors name the file and field.

## Tests

```
python3 tests/test_sim.py
# or, if pytest is installed:
python3 -m pytest tests/ -v
```

## Method notes / assumptions (beyond SCHEMA.md's literal text)

- **Paid channels**: CAC base and CAC-improvement-per-month are sampled once per run
  (triangular) and applied across all 6 months via
  `CAC_m = CAC_base × (1 − improvement)^(m−1) × (1 + k × spend_m)`. New customers =
  `spend_m / CAC_m` (0 if spend is 0 that month).
- **Organic channels**: one shared uniform percentile is drawn per run per channel and
  mapped through each month's own triangular inverse-CDF (`low/typical/high`), so a
  "good" run stays good across all 6 months instead of month-to-month noise cancelling
  out.
- **Repeat orders**: modelled as expected values, not individually simulated repeat
  events. A customer acquired in month `j` contributes
  `customers_j × effective_p_i` repeat orders in month `j+i`, where `effective_p_i =
  clip(p_i × (1 + sub_share × (multiplier − 1)), 0, 1)` and `p_i`/`sub_share`/
  `multiplier` are sampled once per run.
- **WhatsApp marketing cost**: applied to the *cumulative* (running-total) customer
  base each month, not just new customers that month — this is a retention/engagement
  cost on the whole active base, which is the more realistic reading of "per customer
  per month."
- **RTO**: `rto_loss = gross_revenue × cod_share × rto_rate` is subtracted from revenue;
  fulfilment cost is still charged on every order (including ones that RTO), per
  `orders_m × fulfilment_cost_per_order`.
- **Repeat rate @90d/@180d**: `effective_p_i` depends only on "months since first
  purchase" (`i`), not on which acquisition month a cohort is in, so the "cohort-weighted
  average over month-1..3 cohorts" the schema calls for collapses to a single value:
  `1 − Π_{i=1}^{3}(1 − effective_p_i)` for @90d, and `1 − Π_{i=1}^{5}(1 − effective_p_i)`
  (month-1 cohort only) for @180d. Both are still random per Monte Carlo run (since
  `effective_p_i` is sampled), so they get their own P10/P50/P90.
- **Payback month**: first month where cumulative contribution ≥ cumulative marketing
  spend, evaluated per run. Runs that never pay back within 6 months get the label
  "not within 6m" (their P10/P50/P90 shows this whenever that percentile itself didn't
  pay back). `share_within_6m` in `summary.json` reports what fraction of runs did.
- **Marketing spend** (`fixed_costs + paid spend`) is a deterministic budget input per
  scenario, not sampled — so its P10/P50/P90 in `monthly.csv`/`summary.md` are equal.
