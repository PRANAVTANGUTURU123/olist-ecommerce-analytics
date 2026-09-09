"""Consolidates sql/results/*.csv (+ a couple of quick DuckDB queries for
overall totals) into one JSON blob for the standalone HTML dashboard."""
import json
import duckdb
import pandas as pd

R = "sql/results"


def rows(name):
    return pd.read_csv(f"{R}/{name}.csv").to_dict("records")


con = duckdb.connect("data/olist.duckdb", read_only=True)
overall_reviews = con.execute(
    "SELECT ROUND(AVG(review_score), 3) AS avg_review_score, COUNT(*) AS total_reviews FROM fact_reviews"
).df().to_dict("records")[0]
con.close()

monthly = rows("01_sales_revenue_trends__monthly_revenue_trend")
# Sept 2018 is a single-order data-collection-cutoff artifact, not a real data point
monthly_clean = [m for m in monthly if m["year_month"] != "2018-09"]
total_revenue = sum(m["revenue"] for m in monthly_clean)
total_orders = sum(m["orders"] for m in monthly_clean)

delivery = rows("03_delivery_logistics__overall_delivery_stats")[0]
retention_headline = rows("07_customer_retention__repeat_customer_headline_rate")[0]

data = {
    "kpis": {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "revenue_per_order": round(total_revenue / total_orders, 2),
        "avg_review_score": overall_reviews["avg_review_score"],
        "pct_late_orders": delivery["pct_late"],
        "avg_delivery_days": delivery["avg_actual_days"],
        "avg_estimated_days": delivery["avg_estimated_days"],
        "avg_days_ahead_of_estimate": -delivery["avg_delta_days"],
        "total_customers": retention_headline["total_customers"],
        "pct_repeat_customers": retention_headline["pct_repeat_customers"],
    },
    "monthly_revenue_trend": monthly_clean,
    "revenue_by_weekday": rows("01_sales_revenue_trends__revenue_by_weekday"),
    "order_status_breakdown": rows("01_sales_revenue_trends__order_status_breakdown"),
    "top_categories": rows("02_category_performance__top_20_categories_by_revenue"),
    "worst_review_categories": rows("02_category_performance__categories_with_worst_reviews"),
    "late_rate_by_state": rows("03_delivery_logistics__late_rate_by_customer_state"),
    "late_rate_by_category": rows("03_delivery_logistics__late_rate_by_category"),
    "worst_sellers_late": rows("03_delivery_logistics__worst_sellers_by_late_rate"),
    "review_vs_delay": rows("03_delivery_logistics__review_score_vs_delivery_delay"),
    "customers_by_state": rows("04_regional_analysis__customers_by_state"),
    "sellers_by_state": rows("04_regional_analysis__sellers_by_state"),
    "shipping_time_by_state": rows("04_regional_analysis__avg_shipping_time_by_customer_state"),
    "interstate_vs_intrastate": rows("04_regional_analysis__interstate_vs_intrastate_shipping"),
    "payment_type_breakdown": rows("05_payment_behavior__payment_type_breakdown"),
    "installment_bucket": rows("05_payment_behavior__order_value_vs_installments_bucket"),
    "seller_scorecard": rows("06_seller_performance__seller_scorecard"),
    "top_sellers": rows("06_seller_performance__top_sellers_by_revenue"),
    "revenue_at_risk": rows("06_seller_performance__revenue_at_risk_from_poor_sellers")[0],
    "orders_per_customer": rows("07_customer_retention__orders_per_customer_distribution"),
    "revenue_share_repeat": rows("07_customer_retention__revenue_share_repeat_vs_onetime"),
    "days_between_orders": rows("07_customer_retention__days_between_repeat_orders")[0],
}

with open("dashboard/dashboard_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=1)

print("wrote dashboard/dashboard_data.json")
print(json.dumps(data["kpis"], indent=2))
