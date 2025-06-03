import os
import duckdb
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env if present
load_dotenv()

MOTHERDUCK_TOKEN = os.getenv('MOTHERDUCK_TOKEN')
if not MOTHERDUCK_TOKEN:
    raise ValueError("Mother Duck API token not found. Set MOTHERDUCK_TOKEN as an environment variable.")

# Connection string for Mother Duck (connect directly to md:my_db)
conn = duckdb.connect(f"md:my_db?motherduck_token={MOTHERDUCK_TOKEN}")

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

SQL_QUERY = """
/* ───────────────────────────────────────────────
   0) HubSpot companies → ONE row per domain,
      preferring rows that already have an owner_id
   ─────────────────────────────────────────────── */
WITH hs_dedup AS (
  SELECT *
  FROM (
    SELECT
      properties_domain                        AS domain,
      properties_name                          AS hs_name,
      properties_hubspot_owner_id              AS owner_id,
      ROW_NUMBER() OVER (
        PARTITION BY properties_domain
        ORDER BY (properties_hubspot_owner_id IS NULL) ASC, id
      ) AS rn
    FROM hubspot.main.companies
    WHERE properties_domain IS NOT NULL
  )
  WHERE rn = 1
),

/* ───────────────────────────────────────────────
   1) Clean platform.companies.website to bare domain
   ─────────────────────────────────────────────── */
cleaned_companies AS (
  SELECT
    c.id    AS company_id,
    LOWER(
      REGEXP_REPLACE(
        REGEXP_REPLACE(COALESCE(c.website, ''), '^https?://(www\\.)?', ''),
        '/.*$',
        ''
      )
    )       AS cleaned_domain,
    c.name  AS company_name            -- used only in fallback
  FROM platform.companies c
),

/* ───────────────────────────────────────────────
   2) One row per TEST with owner e-mail (dedup logic)
   ─────────────────────────────────────────────── */
per_test AS (
  SELECT
    ow.email                                   AS owner_email,
    DATE_TRUNC('month', ord.ordered_at)        AS revenue_month,
    tst.price
      + COALESCE(tst.turnaround_fee_amount,0)
      + COALESCE(tst.composite_fee_amount,0)   AS full_price
  FROM platform.tests   AS tst
  JOIN platform.samples AS smp ON smp.id = tst.sample_id
  JOIN platform.orders  AS ord ON ord.id = smp.order_id
  JOIN cleaned_companies   cc  ON cc.company_id = ord.company_id

  /* primary domain match */
  LEFT JOIN hs_dedup hsd
    ON hsd.domain = cc.cleaned_domain

  /* fallback name match (only if primary row has no owner) */
  LEFT JOIN hs_dedup hsd_name
    ON hsd.owner_id IS NULL
   AND LOWER(hsd_name.hs_name) = LOWER(cc.company_name)

  /* owners table for e-mail */
  LEFT JOIN hubspot.main.owners ow
    ON ow.id = COALESCE(hsd.owner_id, hsd_name.owner_id)

  /* keep only Jan-May 2025 */
  WHERE DATE_TRUNC('month', ord.ordered_at) BETWEEN DATE '2025-01-01'
                                               AND     DATE '2025-05-01'
),

/* ───────────────────────────────────────────────
   3) Pivot Jan–May totals per owner
   ─────────────────────────────────────────────── */
owner_totals AS (
  SELECT
    COALESCE(owner_email, '(no owner)')           AS owner_email,

    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-01-01') AS jan_2025,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-02-01') AS feb_2025,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-03-01') AS mar_2025,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-04-01') AS apr_2025,
    SUM(full_price) FILTER (WHERE revenue_month = DATE '2025-05-01') AS may_2025
  FROM per_test
  GROUP BY owner_email
)

SELECT *
FROM   owner_totals
ORDER  BY owner_email;
"""

# Run the query and fetch results
df = conn.execute(SQL_QUERY).fetchdf()

# Save to JSON
output_path = "revenue_data.json"
df.to_json(output_path, orient="records")
print(f"Saved revenue data to {output_path}")

# Write last updated timestamp
with open("last_updated.txt", "w") as f:
    f.write(datetime.now().isoformat())
print("Updated last_updated.txt with current timestamp.") 