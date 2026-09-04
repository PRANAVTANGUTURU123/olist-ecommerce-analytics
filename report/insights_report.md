# Olist E-Commerce — Business Insights Report

*Data: ~99k orders, Sept 2016 – Aug 2018 (Brazilian marketplace). Analysis via
SQL (DuckDB) over a cleaned star schema; full queries in `/sql`, full
cleaning pipeline in `/notebooks` and `/scripts`.*

## 1. Delivery delay is the single biggest lever on customer satisfaction

**Problem:** Review scores vary widely across orders — is delivery
performance actually driving that, or is it noise?

**Analysis:** Bucketing orders by `actual delivery date − estimated delivery
date` and averaging review score per bucket (`sql/03_delivery_logistics.sql`,
`review_score_vs_delivery_delay`):

| Delivery outcome | Orders | Avg. review score |
|---|---|---|
| 7+ days early | 70,758 | 4.32 |
| On time / early | 17,216 | 4.20 |
| 1–3 days late | 2,621 | 3.77 |
| 4–7 days late | 1,770 | 2.32 |
| 8+ days late | 3,242 | 1.73 |

A delivery that's 8+ days late drags the average score down by **2.6 stars**
versus early delivery. Overall, 8.1% of delivered orders arrive late, but
Olist's estimated-delivery windows also run generous — the average order is
delivered **11.2 days ahead of the estimate** (12.6 actual days vs. 23.7
estimated), which cushions the late-order impact but also suggests padding
that could be tightened for a faster-feeling customer experience without
increasing the late rate.

Lateness is not evenly distributed: **AL (23.9%), MA (19.7%), and PI
(16.0%)** customer states see late rates 2–4x the national average, while
**SP (5.9%) and MG (5.6%)** — the states closest to Brazil's seller
concentration — barely see it. Shipping between states nearly doubles
delivery time (15.0 days interstate vs. 7.9 days same-state).

**Recommendation:** Prioritize logistics investment (regional fulfillment
partners, carrier SLAs) in the AL/MA/PI/CE corridor, where lateness is both
most frequent and (per the same-state finding) most fixable by shortening
physical shipping distance. Treat any order projected to land in the "4+
days late" band as an intervention trigger (proactive customer comms,
carrier escalation) given the outsized review-score cliff at that threshold.

## 2. Revenue is healthy and growing, but concentrated in a handful of categories and sellers

**Problem:** Where does the business's revenue actually come from, and how
exposed is it to a small number of categories or sellers underperforming?

**Analysis:** Monthly revenue grew from ~R$51k (Oct 2016) to a steady
~R$1.0–1.2M/month through 2018, with a clear Black Friday spike in **Nov
2017** (R$1.17M, +36% over Oct). `health_beauty`, `watches_gifts`, and
`bed_bath_table` are the top 3 categories by revenue (R$1.26M, R$1.20M, and
R$1.04M respectively), together ~11% of all product revenue.

On the seller side (`sql/06_seller_performance.sql`), a **7.0% revenue
share (R$778k of R$11.1M scored)** flows through sellers who fail an
either/or quality bar — average review score under 3.5, or a late-delivery
rate over 20% (min. 20 orders). One seller in particular has a 92% late rate
across 25 orders.

**Recommendation:** Treat the ~65 flagged sellers as a retention-risk list —
either coach them (delivery SLAs, packaging guidance) or reduce their
marketplace visibility, since they're actively depressing review scores on
revenue Olist would otherwise keep. On the category side, `office_furniture`
stands out as a high-volume (1,272 orders) but low-satisfaction category
(3.49 avg. review) worth a root-cause review (damage in transit? sizing
mismatches?) given its scale.

## 3. Repeat-purchase behavior is a real but minor revenue driver — not a retention story yet

**Problem:** How much of Olist's revenue comes from repeat customers, using
`customer_unique_id` (the true person-level key) rather than `customer_id`
(unique per order)?

**Analysis:** Only **3.0% of customers (2,888 of 94,990)** placed more than
one order in this ~2-year window, but they contributed a
disproportionate **5.7% of revenue** (R$890k of R$15.7M) — repeat customers
are worth more per head, they're just rare. Among customers who did repeat,
the median gap between orders is **29 days**.

**Caveat:** this dataset is a fixed historical snapshot (Sept 2016–Aug
2018), so "one order in-window" doesn't necessarily mean "one order ever" —
some of that 97% may have simply ordered again after the data cutoff.
Treat this as a directional read on repeat-purchase economics, not a
CLV/retention KPI to optimize against directly.

**Recommendation:** Don't build a retention program on this alone — the
signal is real (repeat customers spend more) but too thin in this dataset to
size a retention investment. If retention becomes a strategic priority,
instrument future purchases with the same `customer_unique_id` and revisit
this analysis on a rolling window.

## 4. Payment behavior: installments are the default, not the exception

**Problem:** How are customers financing purchases, and does that affect
order value?

**Analysis:** Credit card dominates (78.3% of payment value; 76,505 orders),
followed by boleto (17.9%). Among credit-card payments, installment count
correlates directly with basket size: 1-installment (upfront) orders average
**R$95.87**, while 13+-installment orders average **R$410.31** — a ~4.3x
difference (`sql/05_payment_behavior.sql`).

**Recommendation:** Installments are effectively how larger baskets get
financed on this platform — any pricing or promo strategy for higher-value
items (furniture, electronics) should assume and actively surface
installment options at checkout, since customers are already self-selecting
into them for bigger purchases.

---
*Full query set: `/sql`. Full cleaning + EDA notebook: `/notebooks`. Power BI
build spec (data model, DAX, visual layout): `/dashboard/powerbi_spec.md`.*
