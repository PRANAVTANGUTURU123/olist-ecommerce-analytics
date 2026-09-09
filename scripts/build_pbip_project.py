"""
Generates a Power BI Desktop Project (.pbip) for the Olist star schema:
a full semantic model (9 tables, all relationships, all 15 DAX measures)
with a single blank report page to open into. This is the "hard part"
(data model + DAX) done in code, so opening the .pbip in Power BI Desktop
lands you straight at "ready to build visuals."

EXPERIMENTAL: hand-authored .pbip/TMDL files can't be validated without
Power BI Desktop itself. If Power BI reports the file needs repair, fall
back to manually importing data/processed/*.csv as before.

Run: py scripts/build_pbip_project.py
"""
import os
import uuid
import pandas as pd

PROJECT_DIR = "dashboard/powerbi_project"
PROJECT_NAME = "OlistDashboard"
DATA_DIR = os.path.abspath("data/processed").replace("/", "\\")

SEM_DIR = f"{PROJECT_DIR}/{PROJECT_NAME}.SemanticModel"
REPORT_DIR = f"{PROJECT_DIR}/{PROJECT_NAME}.Report"


def rid():
    return "r_" + uuid.uuid4().hex[:16]


def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Table definitions: name -> list of (column, pandas_dtype_kind)
# ---------------------------------------------------------------------------
TABLES = [
    "dim_customers", "dim_sellers", "dim_products", "dim_geolocation",
    "dim_date", "dim_orders", "fact_order_items", "fact_payments", "fact_reviews",
]
DATETIME_COLS = {
    "purchase_ts", "approved_ts", "delivered_carrier_ts", "delivered_customer_ts",
    "estimated_delivery_ts", "purchase_date", "date", "shipping_limit_date",
    "review_creation_date", "review_answer_timestamp",
}
# is_late has nulls (blank for non-delivered orders), which makes pandas read it
# as dtype=object instead of bool - force it here so it imports as a real
# boolean in Power BI (the "Late Orders" measure depends on this).
BOOLEAN_COLS = {"is_late", "is_weekend", "has_comment"}


def tmdl_type(dtype, colname):
    if colname in BOOLEAN_COLS:
        return "boolean", "type logical"
    if colname in DATETIME_COLS:
        return "dateTime", "type datetime"
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean", "type logical"
    if pd.api.types.is_integer_dtype(dtype):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(dtype):
        return "double", "type number"
    return "string", "type text"


def build_table_tmdl(name):
    df = pd.read_csv(f"data/processed/{name}.csv", nrows=500)
    cols = list(df.columns)
    lines = [f"table {name}", f"\tlineageTag: {uuid.uuid4()}", ""]
    transform_pairs = []
    for col in cols:
        dtype_name, m_type = tmdl_type(df[col].dtype, col)
        summarize = "sum" if dtype_name in ("int64", "double") and col.endswith(("_id", "_seq", "_sequential")) is False and dtype_name != "string" else "none"
        # numeric measures-of-identity (ids, sequentials) should not auto-sum
        if col.endswith("_id") or col in ("order_item_seq", "payment_sequential", "zip_code_prefix"):
            summarize = "none"
        lines.append(f"\tcolumn {col}")
        lines.append(f"\t\tdataType: {dtype_name}")
        lines.append(f"\t\tlineageTag: {uuid.uuid4()}")
        lines.append(f"\t\tsummarizeBy: {summarize}")
        lines.append(f'\t\tsourceColumn: {col}')
        lines.append("")
        lines.append("\t\tannotation SummarizationSetBy = Automatic")
        lines.append("")
        transform_pairs.append(f'{{"{col}", {m_type}}}')

    n = len(cols)
    csv_path = f"{DATA_DIR}\\{name}.csv"
    transform_list = ", ".join(transform_pairs)
    m_lines = [
        "\tpartition " + name + " = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\t\tlet",
        f'\t\t\t\t    Source = Csv.Document(File.Contents("{csv_path}"),[Delimiter=",", Columns={n}, Encoding=65001, QuoteStyle=QuoteStyle.None]),',
        '\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
        f'\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{{transform_list}}})',
        "\t\t\t\tin",
        '\t\t\t\t    #"Changed Type"',
        "",
        "\tannotation PBI_ResultType = Table",
        "",
    ]
    return "\n".join(lines + m_lines)


MEASURES = [
    ("Revenue", """CALCULATE(
    SUMX(fact_order_items, fact_order_items[price] + fact_order_items[freight_value]),
    NOT(dim_orders[order_status] IN {"canceled", "unavailable"})
)""", '"\\$#,0"'),
    ("Product Revenue", """CALCULATE(
    SUM(fact_order_items[price]),
    NOT(dim_orders[order_status] IN {"canceled", "unavailable"})
)""", '"\\$#,0"'),
    ("Orders", """CALCULATE(
    DISTINCTCOUNT(fact_order_items[order_id]),
    NOT(dim_orders[order_status] IN {"canceled", "unavailable"})
)""", "0"),
    ("Revenue per Order", "DIVIDE([Revenue], [Orders])", '"\\$#,0.00"'),
    ("Avg Review Score", "AVERAGE(fact_reviews[review_score])", "0.00"),
    ("Delivered Orders", 'CALCULATE(COUNTROWS(dim_orders), NOT ISBLANK(dim_orders[delivered_customer_ts]))', "0"),
    ("Avg Delivery Days", 'CALCULATE(AVERAGE(dim_orders[delivery_days_actual]), NOT ISBLANK(dim_orders[delivered_customer_ts]))', "0.0"),
    ("Late Orders", 'CALCULATE(COUNTROWS(dim_orders), dim_orders[is_late] = TRUE)', "0"),
    ("Pct Late Orders", "DIVIDE([Late Orders], [Delivered Orders])", "0.0%"),
    ("Total Payment Value", "SUM(fact_payments[payment_value])", '"\\$#,0"'),
    ("Avg Installments", 'CALCULATE(AVERAGE(fact_payments[installments]), fact_payments[payment_type] = "credit_card")', "0.0"),
    ("Repeat Customers", """CALCULATE(
    DISTINCTCOUNT(dim_customers[customer_unique_id]),
    FILTER(
        VALUES(dim_customers[customer_unique_id]),
        CALCULATE(DISTINCTCOUNT(dim_orders[order_id])) > 1
    )
)""", "0"),
    ("Total Customers", "DISTINCTCOUNT(dim_customers[customer_unique_id])", "0"),
    ("Pct Repeat Customers", "DIVIDE([Repeat Customers], [Total Customers])", "0.0%"),
    ("Revenue LY", "CALCULATE([Revenue], SAMEPERIODLASTYEAR(dim_date[date]))", '"\\$#,0"'),
    ("Revenue MoM %", """VAR CurrM = [Revenue]
VAR PrevM = CALCULATE([Revenue], DATEADD(dim_date[date], -1, MONTH))
RETURN DIVIDE(CurrM - PrevM, PrevM)""", "0.0%"),
]


def build_measures_tmdl():
    lines = ["table _Measures", f"\tlineageTag: {uuid.uuid4()}", ""]
    for name, expr, fmt in MEASURES:
        qname = f"'{name}'" if " " in name or "%" in name else name
        lines.append(f"\tmeasure {qname} = ```")
        for l in expr.split("\n"):
            lines.append("\t\t" + l)
        lines.append("\t\t```")
        lines.append(f"\t\tformatString: {fmt}")
        lines.append(f"\t\tlineageTag: {uuid.uuid4()}")
        lines.append("")
    lines += [
        "\tpartition _Measures = calculated",
        "\t\tmode: import",
        "\t\tsource = {(1)}",
        "",
        "\tannotation PBI_ResultType = Table",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Relationships (matches what was built manually in the Power BI walkthrough)
# ---------------------------------------------------------------------------
RELATIONSHIPS = [
    dict(frm="fact_order_items.order_id", to="dim_orders.order_id"),
    dict(frm="fact_order_items.product_id", to="dim_products.product_id"),
    dict(frm="fact_order_items.seller_id", to="dim_sellers.seller_id"),
    dict(frm="dim_orders.customer_id", to="dim_customers.customer_id", one_to_one=True),
    dict(frm="fact_payments.order_id", to="dim_orders.order_id"),
    dict(frm="fact_reviews.order_id", to="dim_orders.order_id"),
    dict(frm="dim_orders.purchase_date", to="dim_date.date"),
    dict(frm="dim_customers.zip_code_prefix", to="dim_geolocation.zip_code_prefix"),
    dict(frm="dim_sellers.zip_code_prefix", to="dim_geolocation.zip_code_prefix", inactive=True),
]


def build_relationships_tmdl():
    lines = []
    for r in RELATIONSHIPS:
        lines.append(f"relationship {rid()}")
        if r.get("one_to_one"):
            lines.append("\tfromCardinality: one")
            lines.append("\ttoCardinality: one")
        if r.get("inactive"):
            lines.append("\tisActive: false")
        lines.append(f"\tfromColumn: {r['frm']}")
        lines.append(f"\ttoColumn: {r['to']}")
        lines.append("")
    return "\n".join(lines)


def build_model_tmdl():
    order = TABLES + ["_Measures"]
    refs = "\n".join(f"ref table {t}" for t in order)
    query_order = ", ".join(f'"{t}"' for t in order)
    return f"""model Model
\tculture: en-US
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: en-US
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

annotation PBI_QueryOrder = [{query_order}]

{refs}
ref cultures/en-US

"""


def build_culture_tmdl():
    return """cultureInfo en-US

\tlinguisticMetadata = ```
\t\t{
\t\t  "Version": "1.0.0",
\t\t  "Language": "en-US"
\t\t}
\t\t```
\t\tcontentType: json
"""


DATABASE_TMDL = """database Model
\tcompatibilityLevel: 1567

"""

PBISM = '{\n  "version": "4.2"\n}\n'

PLATFORM_SEMANTIC = """{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "SemanticModel",
    "displayName": "OlistDashboard"
  },
  "config": {
    "version": "2.0",
    "logicalId": "%s"
  }
}
""" % uuid.uuid4()

PLATFORM_REPORT = """{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "Report",
    "displayName": "OlistDashboard"
  },
  "config": {
    "version": "2.0",
    "logicalId": "%s"
  }
}
""" % uuid.uuid4()

PBIP_POINTER = """{
  "version": "1.0",
  "artifacts": [
    { "report": { "path": "%s.Report" } }
  ],
  "settings": { "enableAutoRecovery": true }
}
""" % PROJECT_NAME

DEFINITION_PBIR = """{
  "version": "4.0",
  "datasetReference": {
    "byPath": {
      "path": "../%s.SemanticModel"
    }
  }
}
""" % PROJECT_NAME

REPORT_JSON = """{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.2.0/schema.json",
  "themeCollection": {
    "baseTheme": {
      "name": "CY24SU10",
      "type": "SharedResources"
    }
  },
  "layoutOptimization": "None",
  "resourcePackages": [],
  "settings": {}
}
"""

PAGE_ID = "overview" + uuid.uuid4().hex[:8]

PAGES_JSON = """{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
  "pageOrder": ["%s"],
  "activePageName": "%s"
}
""" % (PAGE_ID, PAGE_ID)

PAGE_JSON = """{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.4.0/schema.json",
  "name": "%s",
  "displayName": "Overview",
  "displayOption": "FitToPage",
  "height": 720,
  "width": 1280
}
""" % PAGE_ID


def main():
    for t in TABLES:
        w(f"{SEM_DIR}/definition/tables/{t}.tmdl", build_table_tmdl(t))
    w(f"{SEM_DIR}/definition/tables/_Measures.tmdl", build_measures_tmdl())
    w(f"{SEM_DIR}/definition/relationships.tmdl", build_relationships_tmdl())
    w(f"{SEM_DIR}/definition/model.tmdl", build_model_tmdl())
    w(f"{SEM_DIR}/definition/database.tmdl", DATABASE_TMDL)
    w(f"{SEM_DIR}/definition/cultures/en-US.tmdl", build_culture_tmdl())
    w(f"{SEM_DIR}/definition.pbism", PBISM)
    w(f"{SEM_DIR}/.platform", PLATFORM_SEMANTIC)

    w(f"{REPORT_DIR}/definition.pbir", DEFINITION_PBIR)
    w(f"{REPORT_DIR}/definition/report.json", REPORT_JSON)
    w(f"{REPORT_DIR}/definition/pages/pages.json", PAGES_JSON)
    w(f"{REPORT_DIR}/definition/pages/{PAGE_ID}/page.json", PAGE_JSON)
    w(f"{REPORT_DIR}/.platform", PLATFORM_REPORT)

    w(f"{PROJECT_DIR}/{PROJECT_NAME}.pbip", PBIP_POINTER)

    print(f"Wrote Power BI project to {PROJECT_DIR}/")
    print(f"Open {PROJECT_DIR}/{PROJECT_NAME}.pbip in Power BI Desktop.")


if __name__ == "__main__":
    main()
