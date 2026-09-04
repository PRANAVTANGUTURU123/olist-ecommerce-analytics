"""
Executes every .sql file in /sql against data/olist.duckdb.

Each .sql file is split into named blocks using a comment marker:
    -- ==== query_name ====
Each block's result is saved to sql/results/<file_stem>__<query_name>.csv
and a preview is printed to stdout.

Run: py sql/run_queries.py
"""
import glob
import os
import re
import duckdb

DB_PATH = "data/olist.duckdb"
SQL_DIR = "sql"
RESULTS_DIR = "sql/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

MARKER = re.compile(r"^--\s*====\s*(\w+)\s*====\s*$", re.MULTILINE)


def split_named_queries(sql_text):
    """Split a .sql file into {name: query_string} using '-- ==== name ====' markers."""
    matches = list(MARKER.finditer(sql_text))
    blocks = {}
    for i, m in enumerate(matches):
        name = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(sql_text)
        query = sql_text[start:end].strip().rstrip(";")
        if query:
            blocks[name] = query
    return blocks


def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    sql_files = sorted(glob.glob(os.path.join(SQL_DIR, "*.sql")))

    for path in sql_files:
        stem = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        queries = split_named_queries(text)
        if not queries:
            continue
        print(f"\n{'=' * 70}\n{stem}\n{'=' * 70}")
        for name, query in queries.items():
            df = con.execute(query).df()
            out_path = os.path.join(RESULTS_DIR, f"{stem}__{name}.csv")
            df.to_csv(out_path, index=False)
            print(f"\n--- {name} ({len(df)} rows) -> {out_path} ---")
            print(df.head(10).to_string(index=False))

    con.close()


if __name__ == "__main__":
    main()
