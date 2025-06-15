import os
import duckdb
import json
from dotenv import load_dotenv
from datetime import datetime
import sys

print("[fetch_revenue_data.py] Script started.")

# Load environment variables from .env if present
load_dotenv()

MOTHERDUCK_TOKEN = os.getenv('MOTHERDUCK_TOKEN')
if not MOTHERDUCK_TOKEN:
    print("[fetch_revenue_data.py] ERROR: Mother Duck API token not found. Set MOTHERDUCK_TOKEN as an environment variable.")
    sys.exit(1)

# Connection string for Mother Duck (connect directly to md:my_db)
print(f"[fetch_revenue_data.py] Connecting to MotherDuck with token: {MOTHERDUCK_TOKEN[:6]}... (truncated)")
conn = duckdb.connect(f"md:my_db?motherduck_token={MOTHERDUCK_TOKEN}")
print("[fetch_revenue_data.py] Connected to MotherDuck.")

# Test: List all tables in the main schema
print("Listing tables in 'main' schema:")
tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
for table in tables:
    print(table[0])

# Test: Select one row from main.tests
print("\nTesting direct access to main.tests:")
try:
    test_row = conn.execute("SELECT * FROM main.tests LIMIT 1;").fetchone()
    print("Sample row from main.tests:", test_row)
except Exception as e:
    print("Error accessing main.tests:", e)

# Test: Select one row from main.orders
print("\nTesting direct access to main.orders:")
try:
    test_row = conn.execute("SELECT * FROM main.orders LIMIT 1;").fetchone()
    print("Sample row from main.orders:", test_row)
except Exception as e:
    print("Error accessing main.orders:", e)

# Test: Select one row from main.samples
print("\nTesting direct access to main.samples:")
try:
    test_row = conn.execute("SELECT * FROM main.samples LIMIT 1;").fetchone()
    print("Sample row from main.samples:", test_row)
except Exception as e:
    print("Error accessing main.samples:", e)

# Test: Select one row from platform.tests
print("\nTesting direct access to platform.tests:")
try:
    test_row = conn.execute("SELECT * FROM platform.tests LIMIT 1;").fetchone()
    print("Sample row from platform.tests:", test_row)
except Exception as e:
    print("Error accessing platform.tests:", e)

SQL_QUERY = '''
WITH hs_dedup AS (
  SELECT
    properties_domain,
    properties_name,
    properties_hubspot_owner_id AS owner_id
  FROM (
    SELECT
      properties_domain,
      properties_name,
      properties_hubspot_owner_id,
      ROW_NUMBER() OVER (
        PARTITION BY properties_domain
        ORDER BY (properties_hubspot_owner_id IS NULL) ASC, id
      ) AS rn
    FROM hubspot.main.companies
    WHERE properties_domain IS NOT NULL
  ) sub
  WHERE rn = 1
),

per_test AS (
  SELECT
    ow.email                          AS owner_email,
    cc.name                           AS company_name,
    DATE_TRUNC(
      'month',
      COALESCE(ord.ordered_at, smp.created_at)
    )                                  AS revenue_month,
    (tst.price
     + COALESCE(tst.turnaround_fee_amount, 0)
     + COALESCE(tst.composite_fee_amount, 0)
    )                                  AS full_price
  FROM platform.tests     AS tst
  JOIN platform.samples   AS smp ON smp.id     = tst.sample_id
  JOIN platform.orders    AS ord ON ord.id     = smp.order_id
  JOIN platform.companies AS cc  ON cc.id      = ord.company_id

  LEFT JOIN hs_dedup AS hsd
    ON hsd.properties_domain = LOWER(
         REGEXP_REPLACE(
           REGEXP_REPLACE(COALESCE(cc.website, ''), '^https?://(www\\.)?', ''),
           '/.*$',
           ''
         )
       )

  LEFT JOIN hs_dedup AS hsd2
    ON hsd.owner_id IS NULL
   AND LOWER(hsd2.properties_name) = LOWER(cc.name)

  LEFT JOIN hubspot.main.owners AS ow
    ON ow.id = COALESCE(hsd.owner_id, hsd2.owner_id)

  WHERE DATE_TRUNC(
          'month',
          COALESCE(ord.ordered_at, smp.created_at)
        ) BETWEEN DATE '2025-01-01' AND DATE '2025-06-01'
    AND ord.status NOT IN (0, 3)
),

owner_company_totals AS (
  SELECT
    COALESCE(owner_email, '(no owner)')          AS owner_email,
    -- company_name,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-01-01') AS jan_2025,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-02-01') AS feb_2025,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-03-01') AS mar_2025,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-04-01') AS apr_2025,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-05-01') AS may_2025,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-06-01') AS jun_2025
  FROM per_test
  GROUP BY owner_email--, company_name
)

SELECT *
FROM owner_company_totals
ORDER BY owner_email--, company_name;
'''

print("[fetch_revenue_data.py] Running SQL query...")
df = conn.execute(SQL_QUERY).fetchdf()
print(f"[fetch_revenue_data.py] Query returned {len(df)} rows.")

# Save to JSON
output_path = os.path.abspath("revenue_data.json")
df.to_json(output_path, orient="records")
print(f"[fetch_revenue_data.py] Saved revenue data to {output_path}")

# Write last updated timestamp
with open("last_updated.txt", "w") as f:
    f.write(datetime.now().isoformat())
print("[fetch_revenue_data.py] Updated last_updated.txt with current timestamp.") 