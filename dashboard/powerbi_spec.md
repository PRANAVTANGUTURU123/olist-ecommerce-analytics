# Power BI Dashboard Spec — Olist E-Commerce

This is the build spec for the Power BI Desktop file: exact data model,
relationships, DAX measures, and a page-by-page visual layout. Source data is
`data/processed/*.parquet` (or `.csv` — parquet keeps types clean and loads
faster).

## 1. Import & data model

Import all 9 tables from `data/processed/`:

| Table | Grain | Role |
|---|---|---|
| `dim_orders` | 1 row per order | Fact-like bridge dimension — every other fact keys off `order_id` through this table |
| `fact_order_items` | 1 row per order line item | Primary sales fact |
| `fact_payments` | 1 row per payment installment record | Payment fact |
| `fact_reviews` | 1 row per review | Review fact |
| `dim_customers` | 1 row per `customer_id` | Customer + location |
| `dim_sellers` | 1 row per `seller_id` | Seller + location |
| `dim_products` | 1 row per `product_id` | Product + category |
| `dim_date` | 1 row per calendar day | Time intelligence |
| `dim_geolocation` | 1 row per zip prefix | Lat/lng for map visuals |

**Mark `dim_date` as a Date Table** (Model view → right-click `dim_date` →
"Mark as date table", using the `date` column).

### Relationships

Build these in Model view (all Many-to-One, single direction unless noted):

| From | To | Cardinality |
|---|---|---|
| `fact_order_items[order_id]` | `dim_orders[order_id]` | Many-to-1 |
| `fact_order_items[product_id]` | `dim_products[product_id]` | Many-to-1 |
| `fact_order_items[seller_id]` | `dim_sellers[seller_id]` | Many-to-1 |
| `dim_orders[customer_id]` | `dim_customers[customer_id]` | Many-to-1 |
| `fact_payments[order_id]` | `dim_orders[order_id]` | Many-to-1 |
| `fact_reviews[order_id]` | `dim_orders[order_id]` | Many-to-1 |
| `dim_orders[purchase_date]` | `dim_date[date]` | Many-to-1 |
| `dim_sellers[zip_code_prefix]` | `dim_geolocation[zip_code_prefix]` | Many-to-1 (inactive — see note) |
| `dim_customers[zip_code_prefix]` | `dim_geolocation[zip_code_prefix]` | Many-to-1 |

**Note on geolocation:** activate only the `dim_customers → dim_geolocation`
relationship by default; leave `dim_sellers → dim_geolocation` **inactive**
(Power BI won't allow two active paths converging on the same table from
different sources without ambiguity). Use `USERELATIONSHIP()` in any seller
DAX measure that needs seller-side coordinates.

This gives a clean star: `fact_order_items` and `fact_payments`/`fact_reviews`
all filter through `dim_orders`, which is the natural place to slice by
status, dates, and delivery performance.

## 2. DAX measures

Create a dedicated measures table (New Table → `_Measures`, or a blank query)
to keep them out of the physical tables.

```dax
-- Revenue: exclude canceled/unavailable orders, item price + freight
Revenue =
CALCULATE(
    SUMX(fact_order_items, fact_order_items[price] + fact_order_items[freight_value]),
    dim_orders[order_status] NOT IN {"canceled", "unavailable"}
)

Product Revenue =
CALCULATE(
    SUM(fact_order_items[price]),
    dim_orders[order_status] NOT IN {"canceled", "unavailable"}
)

Orders =
CALCULATE(
    DISTINCTCOUNT(fact_order_items[order_id]),
    dim_orders[order_status] NOT IN {"canceled", "unavailable"}
)

Revenue per Order = DIVIDE([Revenue], [Orders])

Avg Review Score = AVERAGE(fact_reviews[review_score])

Delivered Orders =
CALCULATE(COUNTROWS(dim_orders), NOT ISBLANK(dim_orders[delivered_customer_ts]))

Avg Delivery Days =
CALCULATE(AVERAGE(dim_orders[delivery_days_actual]), NOT ISBLANK(dim_orders[delivered_customer_ts]))

Late Orders =
CALCULATE(COUNTROWS(dim_orders), dim_orders[is_late] = TRUE)

Pct Late Orders = DIVIDE([Late Orders], [Delivered Orders])

Total Payment Value = SUM(fact_payments[payment_value])

Avg Installments =
CALCULATE(AVERAGE(fact_payments[installments]), fact_payments[payment_type] = "credit_card")

-- Repeat-customer rate (caveat metric — see report)
Repeat Customers =
CALCULATE(
    DISTINCTCOUNT(dim_customers[customer_unique_id]),
    FILTER(
        VALUES(dim_customers[customer_unique_id]),
        CALCULATE(DISTINCTCOUNT(dim_orders[order_id])) > 1
    )
)

Total Customers = DISTINCTCOUNT(dim_customers[customer_unique_id])

Pct Repeat Customers = DIVIDE([Repeat Customers], [Total Customers])

-- Time intelligence (needs dim_date marked as date table)
Revenue LY = CALCULATE([Revenue], SAMEPERIODLASTYEAR(dim_date[date]))
Revenue MoM % =
VAR CurrM = [Revenue]
VAR PrevM = CALCULATE([Revenue], DATEADD(dim_date[date], -1, MONTH))
RETURN DIVIDE(CurrM - PrevM, PrevM)
```

## 3. Visual layout plan

**Page 1 — Executive Overview**
- KPI cards (top strip): `Revenue`, `Orders`, `Revenue per Order`, `Avg Review
  Score`, `Pct Late Orders`
- Line/bar combo: `Revenue` and `Orders` by `dim_date[year_month]`
  (monthly trend, matches `sql/01_sales_revenue_trends.sql`)
- Bar chart: `Revenue` by `dim_date[day_name]` (weekday pattern)
- Donut: `order_status` breakdown (share of orders)
- Slicers: date range, `dim_customers[state]`

**Page 2 — Category Performance**
- Bar chart: `Product Revenue` by `dim_products[category_en]`, top 15,
  sorted descending
- Scatter: `Product Revenue` (x) vs `Avg Review Score` (y) by category,
  bubble size = `Orders` — flags high-revenue/low-review categories at a
  glance
- Table: category, orders, product revenue, avg review score, avg item
  price — sortable, matches `sql/02_category_performance.sql`
- Slicer: category

**Page 3 — Delivery & Logistics**
- KPI cards: `Avg Delivery Days`, `Pct Late Orders`, avg estimated days
- Map (filled or bubble): `Pct Late Orders` by customer state (use
  `dim_geolocation` lat/lng or built-in state shape map on `dim_customers[state]`)
- Bar chart: `Pct Late Orders` by `dim_customers[state]`, sorted descending
- Bar chart: `Avg Review Score` by delivery-delay bucket (build a calculated
  column on `dim_orders` bucketing `delivery_delta_days`, mirroring
  `sql/03_delivery_logistics.sql`'s `review_score_vs_delivery_delay`) — this
  is the single most persuasive chart in the deck: on-time ≈ 4.3★, 8+ days
  late ≈ 1.7★
- Table: worst 15 sellers by late rate (min 20 orders)

**Page 4 — Regional Analysis**
- Map: customer count / revenue by state (bubble size = revenue)
- Map or bar: seller count by state (shows the SP-heavy seller
  concentration vs. nationwide customer base)
- Bar chart: `Avg Delivery Days` by customer state
- Card/comparison visual: same-state vs. different-state avg delivery days
  (interstate shipping penalty)

**Page 5 — Payments & Sellers**
- Donut: `Total Payment Value` by `payment_type`
- Column chart: avg payment value by installment bucket (1, 2-3, 4-6, 7-12,
  13+) — shows installments financing bigger baskets
- Table: seller scorecard — seller, state, orders, product revenue, pct
  late, avg review score, filterable by min-order threshold (use a what-if
  parameter or a fixed `FILTER` in the table's visual-level filter, orders
  ≥ 20)
- Card: `Pct Revenue at Risk` (revenue from sellers with avg review < 3.5 OR
  late rate > 20%, min 20 orders — mirrors
  `sql/06_seller_performance.sql`'s `revenue_at_risk_from_poor_sellers`)

**Page 6 — Customer Retention (caveat page)**
- Header text box explaining the caveat: this dataset is a 2016–2018
  snapshot with `customer_unique_id` as the person-level key; only ~3% of
  customers have more than one order in-window, so treat this page as
  directional, not a CLV/retention core metric
- KPI cards: `Total Customers`, `Repeat Customers`, `Pct Repeat Customers`
- Bar chart: customers by order-count bucket (1 / 2 / 3-5 / 6+)
- Bar chart: revenue share, repeat vs. one-time customers

### Formatting conventions
- Use one consistent categorical palette across all pages (see the
  `dataviz` skill's palette if building charts elsewhere; in Power BI, set a
  custom theme JSON so category colors for the same category stay consistent
  page to page)
- Currency format for all revenue measures: `R$ #,##0`
- Percent format for rate measures: `0.0%`
- Every page: a date-range slicer synced across pages (Slicer panel →
  sync visuals)
