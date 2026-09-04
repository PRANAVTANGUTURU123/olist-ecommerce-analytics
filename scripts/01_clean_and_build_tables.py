"""
Olist E-Commerce - Data Cleaning & Star Schema Builder
--------------------------------------------------------
Reads the 9 raw Kaggle CSVs from data/raw/, cleans them, and writes a
Power BI-ready star schema (fact + dimension tables) to data/processed/
as both CSV and Parquet. Also loads the same tables into a DuckDB file
(data/olist.duckdb) that the SQL analysis scripts in /sql query against.

Run: py scripts/01_clean_and_build_tables.py
"""
import os
import pandas as pd
import numpy as np
import duckdb

RAW = "data/raw"
OUT = "data/processed"
os.makedirs(OUT, exist_ok=True)

pd.set_option("display.width", 120)


def log(msg):
    print(f"[clean] {msg}")


def save(df, name):
    """Write a table to both CSV and Parquet in data/processed/."""
    csv_path = os.path.join(OUT, f"{name}.csv")
    pq_path = os.path.join(OUT, f"{name}.parquet")
    df.to_csv(csv_path, index=False)
    df.to_parquet(pq_path, index=False)
    log(f"saved {name}: {df.shape[0]:,} rows x {df.shape[1]} cols -> {csv_path}")
    return df


# ---------------------------------------------------------------------------
# 1. LOAD RAW FILES
# ---------------------------------------------------------------------------
log("loading raw CSVs...")
customers = pd.read_csv(f"{RAW}/olist_customers_dataset.csv")
geolocation = pd.read_csv(f"{RAW}/olist_geolocation_dataset.csv")
order_items = pd.read_csv(f"{RAW}/olist_order_items_dataset.csv")
payments = pd.read_csv(f"{RAW}/olist_order_payments_dataset.csv")
reviews = pd.read_csv(f"{RAW}/olist_order_reviews_dataset.csv")
orders = pd.read_csv(f"{RAW}/olist_orders_dataset.csv")
products = pd.read_csv(f"{RAW}/olist_products_dataset.csv")
sellers = pd.read_csv(f"{RAW}/olist_sellers_dataset.csv")
translation = pd.read_csv(f"{RAW}/product_category_name_translation.csv")

raw_row_counts = {
    "customers": len(customers), "geolocation": len(geolocation),
    "order_items": len(order_items), "payments": len(payments),
    "reviews": len(reviews), "orders": len(orders),
    "products": len(products), "sellers": len(sellers),
}

# ---------------------------------------------------------------------------
# 2. CLEAN INDIVIDUAL TABLES
# ---------------------------------------------------------------------------

# --- orders: parse timestamps, dedupe ---
date_cols = [
    "order_purchase_timestamp", "order_approved_at",
    "order_delivered_carrier_date", "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
for c in date_cols:
    orders[c] = pd.to_datetime(orders[c], errors="coerce")
orders = orders.drop_duplicates(subset="order_id")
log(f"orders: {len(orders):,} rows, {orders.duplicated('order_id').sum()} dup order_ids after dedupe")

# --- products: fill missing category, impute the 2 missing dimension rows ---
products["product_category_name"] = products["product_category_name"].fillna("unknown")
for c in ["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]:
    products[c] = products[c].fillna(products[c].median())
products = products.merge(translation, on="product_category_name", how="left")
products["product_category_name_english"] = (
    products["product_category_name_english"].fillna(products["product_category_name"])
)
products["product_volume_cm3"] = (
    products["product_length_cm"] * products["product_height_cm"] * products["product_width_cm"]
)

# --- geolocation: dedupe ~1M noisy rows down to one row per zip prefix,
#     drop coordinates outside Brazil's bounding box (bad geocodes) ---
BR_LAT = (-34.0, 5.5)
BR_LNG = (-74.5, -32.0)
geo_clean = geolocation[
    geolocation["geolocation_lat"].between(*BR_LAT)
    & geolocation["geolocation_lng"].between(*BR_LNG)
].copy()
dropped_geo = len(geolocation) - len(geo_clean)
geo_dim = (
    geo_clean.groupby("geolocation_zip_code_prefix")
    .agg(
        lat=("geolocation_lat", "mean"),
        lng=("geolocation_lng", "mean"),
        city=("geolocation_city", lambda s: s.mode().iat[0]),
        state=("geolocation_state", lambda s: s.mode().iat[0]),
    )
    .reset_index()
    .rename(columns={"geolocation_zip_code_prefix": "zip_code_prefix"})
)
log(f"geolocation: {len(geolocation):,} raw rows -> dropped {dropped_geo:,} out-of-bounds "
    f"-> {len(geo_dim):,} unique zip prefixes")

# --- reviews: dedupe, build has_comment flag ---
reviews = reviews.drop_duplicates(subset="review_id")
for c in ["review_creation_date", "review_answer_timestamp"]:
    reviews[c] = pd.to_datetime(reviews[c], errors="coerce")
reviews["has_comment"] = reviews["review_comment_message"].notna()

# --- payments, order_items: straightforward, just sanity-check types ---
order_items["shipping_limit_date"] = pd.to_datetime(order_items["shipping_limit_date"], errors="coerce")
payments["payment_value"] = payments["payment_value"].astype(float)

# ---------------------------------------------------------------------------
# 3. ORPHAN-KEY SANITY CHECKS (rows that wouldn't join to their parent)
# ---------------------------------------------------------------------------
orphan_items_orders = (~order_items["order_id"].isin(orders["order_id"])).sum()
orphan_items_products = (~order_items["product_id"].isin(products["product_id"])).sum()
orphan_items_sellers = (~order_items["seller_id"].isin(sellers["seller_id"])).sum()
orphan_orders_customers = (~orders["customer_id"].isin(customers["customer_id"])).sum()
orphan_payments_orders = (~payments["order_id"].isin(orders["order_id"])).sum()
orphan_reviews_orders = (~reviews["order_id"].isin(orders["order_id"])).sum()
log("orphan-key check (should all be 0):")
for name, val in [
    ("order_items -> orders", orphan_items_orders),
    ("order_items -> products", orphan_items_products),
    ("order_items -> sellers", orphan_items_sellers),
    ("orders -> customers", orphan_orders_customers),
    ("payments -> orders", orphan_payments_orders),
    ("reviews -> orders", orphan_reviews_orders),
]:
    log(f"  {name}: {val}")

# ---------------------------------------------------------------------------
# 4. BUILD STAR SCHEMA
# ---------------------------------------------------------------------------

# --- dim_customers ---
dim_customers = customers.rename(columns={
    "customer_zip_code_prefix": "zip_code_prefix",
    "customer_city": "city",
    "customer_state": "state",
})[["customer_id", "customer_unique_id", "zip_code_prefix", "city", "state"]]

# --- dim_sellers ---
dim_sellers = sellers.rename(columns={
    "seller_zip_code_prefix": "zip_code_prefix",
    "seller_city": "city",
    "seller_state": "state",
})[["seller_id", "zip_code_prefix", "city", "state"]]

# --- dim_products ---
dim_products = products.rename(columns={
    "product_category_name": "category_pt",
    "product_category_name_english": "category_en",
    "product_weight_g": "weight_g",
    "product_length_cm": "length_cm",
    "product_height_cm": "height_cm",
    "product_width_cm": "width_cm",
})[["product_id", "category_pt", "category_en", "weight_g", "length_cm",
    "height_cm", "width_cm", "product_volume_cm3"]]

# --- dim_geolocation ---
dim_geolocation = geo_dim[["zip_code_prefix", "lat", "lng", "city", "state"]]

# --- dim_date: full calendar spanning the order history ---
min_date = orders["order_purchase_timestamp"].min().normalize()
max_date = orders["order_purchase_timestamp"].max().normalize()
dim_date = pd.DataFrame({"date": pd.date_range(min_date, max_date, freq="D")})
dim_date["year"] = dim_date["date"].dt.year
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.strftime("%b")
dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m")
dim_date["quarter"] = dim_date["date"].dt.quarter
dim_date["day_name"] = dim_date["date"].dt.strftime("%a")
dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5

# --- dim_orders (order grain "fact-like dimension" that other facts key off) ---
dim_orders = orders.rename(columns={
    "order_purchase_timestamp": "purchase_ts",
    "order_approved_at": "approved_ts",
    "order_delivered_carrier_date": "delivered_carrier_ts",
    "order_delivered_customer_date": "delivered_customer_ts",
    "order_estimated_delivery_date": "estimated_delivery_ts",
}).copy()
dim_orders["purchase_date"] = dim_orders["purchase_ts"].dt.normalize()
dim_orders["delivery_days_actual"] = (
    dim_orders["delivered_customer_ts"] - dim_orders["purchase_ts"]
).dt.total_seconds() / 86400
dim_orders["delivery_days_estimated"] = (
    dim_orders["estimated_delivery_ts"] - dim_orders["purchase_ts"]
).dt.total_seconds() / 86400
# positive delta = delivered later than promised (late); negative = early
dim_orders["delivery_delta_days"] = (
    dim_orders["delivered_customer_ts"] - dim_orders["estimated_delivery_ts"]
).dt.total_seconds() / 86400
dim_orders["is_late"] = (dim_orders["delivery_delta_days"] > 0).astype("boolean")
dim_orders.loc[dim_orders["delivered_customer_ts"].isna(), "is_late"] = pd.NA
dim_orders = dim_orders[[
    "order_id", "customer_id", "order_status", "purchase_ts", "approved_ts",
    "delivered_carrier_ts", "delivered_customer_ts", "estimated_delivery_ts",
    "purchase_date", "delivery_days_actual", "delivery_days_estimated",
    "delivery_delta_days", "is_late",
]]

# --- fact_order_items ---
fact_order_items = order_items.rename(columns={"order_item_id": "order_item_seq"})[[
    "order_id", "order_item_seq", "product_id", "seller_id",
    "shipping_limit_date", "price", "freight_value",
]]

# --- fact_payments ---
fact_payments = payments.rename(columns={"payment_installments": "installments"})[[
    "order_id", "payment_sequential", "payment_type", "installments", "payment_value",
]]

# --- fact_reviews ---
fact_reviews = reviews[[
    "review_id", "order_id", "review_score", "has_comment",
    "review_creation_date", "review_answer_timestamp",
]]

# ---------------------------------------------------------------------------
# 5. SAVE STAR SCHEMA
# ---------------------------------------------------------------------------
save(dim_customers, "dim_customers")
save(dim_sellers, "dim_sellers")
save(dim_products, "dim_products")
save(dim_geolocation, "dim_geolocation")
save(dim_date, "dim_date")
save(dim_orders, "dim_orders")
save(fact_order_items, "fact_order_items")
save(fact_payments, "fact_payments")
save(fact_reviews, "fact_reviews")

# ---------------------------------------------------------------------------
# 6. LOAD INTO DUCKDB FOR THE SQL LAYER
# ---------------------------------------------------------------------------
db_path = "data/olist.duckdb"
if os.path.exists(db_path):
    os.remove(db_path)
con = duckdb.connect(db_path)
tables = {
    "dim_customers": dim_customers, "dim_sellers": dim_sellers,
    "dim_products": dim_products, "dim_geolocation": dim_geolocation,
    "dim_date": dim_date, "dim_orders": dim_orders,
    "fact_order_items": fact_order_items, "fact_payments": fact_payments,
    "fact_reviews": fact_reviews,
}
for name, df in tables.items():
    con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM df")
con.close()
log(f"loaded {len(tables)} tables into {db_path}")

# ---------------------------------------------------------------------------
# 7. SUMMARY
# ---------------------------------------------------------------------------
log("=== raw row counts ===")
for k, v in raw_row_counts.items():
    log(f"  {k}: {v:,}")
log("=== processed star-schema row counts ===")
for name, df in tables.items():
    log(f"  {name}: {len(df):,}")
log("done.")
