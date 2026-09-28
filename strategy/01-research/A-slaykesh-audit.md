# SlayKesh — Factual Audit
Prepared 2026-09-28. All figures INR. Each datum tagged **OBSERVED** (source URL) or **ESTIMATED** (reasoning given). No invented numbers.

---

## 1. Catalogue
Source: OBSERVED, `slaykesh.com/products.json` (9 live products, fetched 2026-09-28) + individual PDPs.

| Product | Type | Size | MRP | Sale price | Disc.% |
|---|---|---|---|---|---|
| Scalp Nurture Hair Serum | Serum | 30 ml | ₹899 | ₹749 | 17% |
| Hydra Shine Hair Mask | Mask | 200 g | ₹799 | ₹649 | 19% |
| Oil-Treated Neem Comb | Accessory | — | ₹199 | ₹199 (no MRP shown) | 0% |
| Healthy Hair Duo (Mask+Serum) | Bundle | — | ₹1,698 | ₹1,249 | 26% |
| Hydra Shine Hair Mask Duo | Bundle | 2×200g | ₹1,598 | ₹1,199 | 25% |
| Scalp Nurture Serum Duo | Bundle | 2×30ml | ₹1,798 | ₹1,349 | 25% |
| Smooth & Detangle Duo (Mask+Comb) | Bundle | — | ₹998 | ₹899 | 10% |
| 3-in-1 Hair Care Combo | Bundle | — | ₹1,799 | ₹1,550 | 14% |
| Complete Hair Repair Kit (PR/spa kit) | Kit | Mask+Serum+Comb | ₹1,999 | ₹1,399 | 30% |

**No standalone "Root Revival" serum SKU found live** — brief names it, site currently sells it as "Scalp Nurture Hair Serum" (product tags include "Slaykesh Hair Treatment"; likely a rename/rebrand). OBSERVED discrepancy, flag for client.

- **Discount code:** `SLAY100` — flat ₹100 off sitewide (OBSERVED, homepage banner).
- **Free shipping threshold:** orders above ₹999 (OBSERVED, homepage banner + PDP).
- **COD:** not stated on homepage/PDPs checked; Flipkart 3P listing explicitly offers COD (OBSERVED, flipkart.com). SlayKesh.com COD status: **not confirmed** — would require reaching checkout with a real cart (not attempted, avoids creating test order).
- **Subscription (subscribe & save):** **No** — no subscription widget found on two PDPs checked or in homepage source (only a Shopify "subscription policy" consent link, unrelated to product subscriptions). OBSERVED (absence).
- **Email/SMS popup:** Yes — newsletter popup present in theme code ("bee-newsletter"), footer also offers "10% discount on prepaid orders" for email signup. OBSERVED.
- All 9 products currently marked `available: true`; no stock-outs detected.

## 2. Proof & Trust
| Signal | Value | Source |
|---|---|---|
| Reviews app | Judge.me (widget detected in theme JS) | OBSERVED, homepage source |
| Scalp Serum rating | 4.3/5, 342 reviews | OBSERVED, PDP |
| Hydra Shine Mask rating | 4.6/5, 278 reviews (78% 5★) | OBSERVED, PDP |
| Before/after imagery | Present on homepage and both PDPs checked (3 sets on Mask PDP) | OBSERVED |
| Named testimonials | Yes, e.g. "Subhashree Tripathy" customer story on Mask PDP | OBSERVED |
| Clinical/derm claims | "Clinically researched," "Dermatologically tested," "60-day hair growth claim," 4 patented actives (Redensyl® 3%, Anagain® 5%, Procapil® 2%, Baicapil® 1%) | OBSERVED, homepage trust bar + serum PDP |
| Certifications | No third-party certification logos (FSSAI/cruelty-free/ISO badges) observed on pages checked — claims are brand-stated, not visibly certified | OBSERVED (absence) |
| Founder story placement | `/pages/about` — full narrative (age 19 motherhood → age 20 hair loss → "hair starts from scalp" → brand launch), linked in main nav; also a dedicated blog post | OBSERVED |

**Gap:** clinical/dermatologist claims are prominent but no visible link to a study, lab report, or dermatologist name/credential on the pages fetched — a substantiation gap if regulators or skeptical buyers probe it.

## 3. Website Funnel
| Element | Finding | Status |
|---|---|---|
| Hero message | Scalp-first positioning; two rotating banners (hair fall / dry-frizzy hair) | OBSERVED |
| Nav | Hair Serum, Hair Mask, Bundles & Combos, Accessory, About Us, Blogs | OBSERVED |
| PDP layout | 8–9 images, before/after, testimonials, FAQ (6 Qs), ingredient breakdown, usage steps | OBSERVED |
| Quiz/diagnostic | A blog post is titled "SlayKesh Product Quiz: Find Your Best Hair Care Fit" but **no quiz widget found on homepage** — likely a content piece, not an interactive tool, or buried/removed | OBSERVED (nav has no quiz link) |
| WhatsApp chat button | Yes, +91 93652 90822, top-right widget (`wa.me/919365290822`) | OBSERVED |
| Email/SMS popup | Yes, newsletter popup + "10% off prepaid" footer offer | OBSERVED |
| Checkout | Standard Shopify checkout (`/cart` and `/checkout` both resolve; native Shopify flow, no visible custom checkout app) | OBSERVED |
| Blog | 12 posts found, **all dated the same day (23 Jul 2026)** — reads as a single bulk content launch, not ongoing cadence; topics: ingredient education, myth-busting, founder story, multilingual posts (Hindi, Odia) | OBSERVED |
| SEO — title tag | "Advanced Scalp Hair Growth Serum \| Best Hair Care Products - Slaykesh" | OBSERVED |
| SEO — meta description | Present, generic ("Discover premium Hair Care Products by Slaykesh...") | OBSERVED |
| Schema markup | Exactly 1 `application/ld+json` block detected on homepage — present but minimal; type not verified in depth | OBSERVED |
| Mobile PageSpeed | **Not obtained** — Google PageSpeed API returned HTTP 429 "daily quota exceeded" on both attempts | Tool unavailable, not ESTIMATED |

## 4. Channels & Marketplaces
| Channel | Handle/URL | Followers/subs | Cadence |
|---|---|---|---|
| Instagram | instagram.com/slaykesh ("Hair Repair & Scalp Care") | Not obtainable — WebFetch returned HTTP 429 and web search indexed no follower count | — |
| YouTube | youtube.com/@SlayKesh | Not obtainable — WebFetch returned only page chrome, no channel stats | — |
| Facebook | facebook.com/profile.php?id=61587847872834 | Not checked in depth | — |
| WhatsApp | +91 93652 90822 (click-to-chat) | n/a | — |

Links confirmed OBSERVED (site footer, home.html source). Follower/subscriber counts and post cadence could **not** be confirmed via WebFetch (rate-limited/blocked) or WebSearch (no indexed figures) — flag as a data gap; recommend manual login-based check by the client team.

**Marketplaces (OBSERVED via web search, listings exist; live price/rating not independently confirmed due to fetch blocks):**
- **Amazon.in** — multiple listings: "SlayKesh Complete Hair Care Kit," "Grow From Root Serum," "Frizz Control Serum" (Amazon PDP fetch returned HTTP 503, could not pull live price/rating).
- **Flipkart** — "Slaykesh Hydrating Hair Mask," "Slaykesh Grow From Roots Serum," plus a "Slaykesh Pearl claw hair clips" listing (accessory outside the D2C site's current catalogue — possible unauthorized/legacy 3P listing; flag for brand-control check). COD offered on Flipkart listing (OBSERVED).
- **Nykaa, Myntra, Meesho** — no listings surfaced in web search. **ESTIMATED absence** (reasoning: targeted site-restricted searches returned zero matching results on all three; could be true absence or simply poor indexing — not certain either way).

## 5. Semrush (SEO/traffic)
**Not available.** `domain_overview` call failed: `no_api_units` — "active Semrush subscription, but does not have enough API units." No organic traffic, keyword, or backlink data obtained. Recommend the client top up Semrush units or supply GA4/Search Console access directly.

## 6. Strengths / Gaps / Quick Wins
**Strengths**
- Clear scalp-first niche with a credible, emotionally strong founder story already written and placed in nav.
- Patented, named actives (Redensyl/Anagain/Procapil/Baicapil) give a defensible clinical-sounding hook competitors without named actives can't easily copy.
- Reasonable review volume (278–342 per hero SKU) and 4.3–4.6★ ratings — real social proof exists, just underused.

**Gaps**
- No subscribe-and-save — pure one-time purchase funnel undermines the brief's repeat-rate KPI directly.
- Blog is a one-day bulk dump, not a cadence — zero ongoing SEO/content momentum since July.
- "Product Quiz" is referenced in a blog title but no live interactive quiz/diagnostic found — a common high-converting PDP tool is missing or hidden.
- Clinical/derm claims have no visible substantiation link (study, lab, derm name) — reputational/regulatory exposure.
- Social follower counts unverifiable from outside — suggests either small/undersized presence or simply gated data; either way, the client hasn't made channel scale legible to a growth partner.
- A "Slaykesh Pearl claw hair clips" listing on Flipkart doesn't match the current site catalogue — possible listing hygiene/brand-control issue.

**Quick wins**
- Launch subscribe-and-save on the two hero SKUs (Serum, Mask) — directly targets the brief's repeat-rate KPI at near-zero cost (Shopify subscription app).
- Turn the existing "Product Quiz" blog concept into an actual on-site diagnostic quiz gating email/WhatsApp capture — reuses content already written.
- Add one visible substantiation line/link for the clinical claims (even a plain "in-vitro/consumer study on file" note) to de-risk the trust bar.

---
*Unresolved data gaps for the wider engagement:* Google PageSpeed mobile score (API quota exhausted), Semrush organic/backlink data (no API units), live Instagram/YouTube follower counts and post cadence (fetch blocked/not indexed), Amazon.in live pricing (503 on fetch), confirmed COD status on slaykesh.com checkout.
