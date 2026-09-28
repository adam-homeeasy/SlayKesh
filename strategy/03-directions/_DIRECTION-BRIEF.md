# Brief for Direction Agents (shared by D1, D2, D3)

You own ONE strategic direction, built on ONE territory from `02-positioning/positioning.md`. Turn it into an executable plan plus simulation inputs. Other agents are writing the other two directions in parallel — write only your own two files.

## Read first
- `strategy/BRIEF.md`
- `strategy/01-research/A-slaykesh-audit.md`, `B-competitors.md`, `C-audience-benchmarks.md`
- `strategy/02-positioning/positioning.md` (your territory in full, plus the matrix and non-negotiables)
- `strategy/04-simulation/SCHEMA.md` (the exact JSON contract for your sim inputs)

## Deliverable 1 — `strategy/03-directions/direction-<N>-<slug>.md` (target 3,500–5,000 words, tables over prose)

1. **The bet in one paragraph.** Why this direction is the lowest-cost, highest-ROI route to revenue and repeat rate in 3–6 months.
2. **Brand positioning execution.** Final positioning statement, hero naming, messaging hierarchy, tone, visual cues, claim fixes (use the non-negotiables).
3. **Instagram.** Objective and KPIs, content pillars with % mix, formats and weekly cadence, founder's role, creator/affiliate programme (tiers, fees vs commission, briefs), community management, DM→WhatsApp handoff, **a 4-week calendar of real post concepts with hooks** (Hinglish where natural).
4. **YouTube.** Shorts vs long-form split, 2–3 named series with episode ideas, cadence, repurposing from IG, search/SEO titles, KPIs.
5. **WhatsApp.** Opt-in sources, automated flows (welcome, diagnosis/quiz, abandoned cart, COD→prepaid nudge, reorder reminder timed to the product cycle, win-back), broadcast cadence, community/channel usage, **monthly message-cost estimate under the per-message pricing that starts on 1 Oct 2026**, BSP choice, 3 sample template messages, KPIs.
6. **Website.** Changes ranked by ROI/effort: offer architecture, subscription or refill, bundles vs. free-shipping threshold, PDP, quiz, reviews, SEO content plan, CRO. KPIs.
7. **Offer and retention architecture.** Entry offer, AOV ladder, repeat mechanism, loyalty. Show how repeat rate specifically is driven.
8. **Execution roadmap.** Weeks 1–4 week by week, then months 2–6. Team and roles with hours/week, **including founder hours/week**. Tools stack with costs.
9. **Budget: minimum and optimum monthly budget.** Line-item tables for both. Say why *min* is the floor (below it the direction doesn't work) and why *opt* is the ceiling for 3–6 months (beyond it marginal returns fall). Say what min cuts versus opt.
10. **Risks, leading indicators and kill/pivot criteria** (what you'd check at day 30, 60 and 90).
11. **Assumptions register.** Every number you feed the sim, with its source or reasoning.

## Deliverable 2 — `strategy/04-simulation/inputs/direction-<N>.json`
Follow SCHEMA.md exactly (6-month arrays, `[low, typical, high]` ranges, scenarios `min` and `opt`). Then:
- If `strategy/04-simulation/validate.py` exists, run it on your file and fix all errors (`python3 strategy/04-simulation/validate.py`, or `python3 strategy/04-simulation/sim.py --validate` — check its README). If it doesn't exist yet, self-check carefully against the schema.
- Do not run the full sim or write into `results/`.

## Calibration rules (all directions — keeps the three comparable)
- **Model incremental impact only.** SlayKesh's existing sales baseline is unknown, so simulate the customers this direction adds.
- **India-realistic paid media.** The research's Meta CPM/CPC figures are global USD proxies and overstate Indian costs. Use India beauty ranges (e.g. CPM roughly ₹120–350) and derive first-order CAC transparently: CPM → CTR → site or WA conversion → CAC. Typical small-brand first-order CAC in Indian D2C beauty is roughly ₹400–1,500. Justify where you land.
- **Repeat realism.** The research's 35–55% 90-day repeat is optimistic for a small brand. Base case is roughly 12–25% at 90 days without structured retention. Your uplift from WhatsApp reminders, subscriptions or regimen design must be explicit and defensible in the assumptions register.
- **Organic ramp realism.** Organic new customers start near zero. Cap them by the reach maths (reach × profile-visit × click × conversion); show the chain in the assumptions register.
- **Shared non-negotiables cost (identical in all three files)** — add as fixed_costs line `"Non-negotiables (shared)"`:
  - min: `[25000, 5000, 5000, 5000, 5000, 5000]`
  - opt: `[40000, 8000, 8000, 8000, 8000, 8000]`
- **Economics defaults** unless your offer design changes them (then justify): gross margin `[0.62, 0.68, 0.74]`, fulfilment + PG + packaging per order `[80, 110, 140]`, COD share `[0.30, 0.40, 0.50]`, RTO on COD `[0.05, 0.09, 0.12]`. Set AOVs from your own offer architecture.
- WhatsApp marketing message ≈ ₹1.02 incl. GST; utility ≈ ₹0.14; BSP ₹1,000–2,600/month.
- Founder time is not a cash cost, but state hours/week and treat it as a constraint.

## Style
Specific to SlayKesh; no generic D2C filler. Cite research files for facts. Mark every number OBSERVED (source) or ESTIMATED (reasoning). INR throughout.
End your final reply with: your min and opt monthly budgets (month-3 run rate), 3 key sim assumptions, and your tool-call count.
