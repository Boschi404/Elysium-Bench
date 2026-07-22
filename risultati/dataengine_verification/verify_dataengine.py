"""
DataScoringEngine verification: 5 pairs of (good, bad) data solutions
Tests that the fixed scorer differentiates between quality solutions and garbage.
Saves all inputs, outputs, and scores in a reproducible format.
"""
import sys, os, json, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from elysium_bench.scoring import DataScoringEngine

TASK_DIR = Path('tasks/data_analysis/T01_data_analysis').resolve()
WEIGHTS = {'correctness': 40, 'completeness': 25, 'efficiency': 15, 'robustness': 10, 'clarity': 10}

pairs = [
    {
        "name": "SQL_sales_report",
        "good": """import pandas as pd
import sqlite3

# Connect to database
conn = sqlite3.connect('sales.db')

# Query: total revenue by category
query = '''
    SELECT
        p.category,
        COUNT(o.order_id) as total_orders,
        SUM(o.amount) as revenue,
        ROUND(AVG(o.amount), 2) as avg_order
    FROM orders o
    JOIN products p ON o.product_id = p.id
    WHERE o.status = 'completed'
    GROUP BY p.category
    HAVING COUNT(o.order_id) > 5
    ORDER BY revenue DESC
'''
df = pd.read_sql(query, conn)

# Handle nulls
try:
    df = df[df['revenue'].notnull()]
except Exception as e:
    print(f'Error: {e}')

# Round values
df['revenue'] = df['revenue'].round(2)
print(df.to_string())
""",
        "bad": """x = 1
y = 2
print(x + y)
""",
    },
    {
        "name": "Pandas_data_cleaning",
        "good": """import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv('data.csv')

# Remove duplicates
df = df.drop_duplicates()

# Handle missing values
try:
    df['age'] = df['age'].fillna(df['age'].median())
    df['name'] = df['name'].fillna('Unknown')
except Exception as e:
    print(f'Error handling nulls: {e}')

# Normalize strings
df['email'] = df['email'].str.lower().str.strip()

# Validate ranges
df = df[(df['age'] >= 0) & (df['age'] <= 150)]

# Remove outliers using IQR
Q1 = df['salary'].quantile(0.25)
Q3 = df['salary'].quantile(0.75)
IQR = Q3 - Q1
df = df[(df['salary'] >= Q1 - 1.5*IQR) & (df['salary'] <= Q3 + 1.5*IQR)]

print(f'Cleaned: {len(df)} rows')
df.to_csv('cleaned.csv', index=False)
""",
        "bad": """import pandas as pd
df = pd.read_csv('data.csv')
print(df)
""",
    },
    {
        "name": "SQL_JOIN_complex",
        "good": """import sqlite3
import pandas as pd

conn = sqlite3.connect('company.db')

# Complex query with multiple joins
query = '''
    SELECT
        e.name as employee,
        d.name as department,
        m.name as manager,
        e.salary,
        ROUND(e.salary * 1.1, 2) as projected_salary
    FROM employees e
    JOIN departments d ON e.dept_id = d.id
    LEFT JOIN employees m ON e.manager_id = m.id
    WHERE e.salary > 50000
    ORDER BY e.salary DESC
    LIMIT 10
'''

try:
    df = pd.read_sql(query, conn)
    # Handle NULL managers
    df['manager'] = df['manager'].fillna('No manager')
    print(df.to_string())
except Exception as e:
    print(f'Query error: {e}')
finally:
    conn.close()
""",
        "bad": """conn = 'database'
result = conn.execute('SELECT *')
print(result)
""",
    },
    {
        "name": "Pandas_merge_transform",
        "good": """import pandas as pd
import numpy as np

# Load multiple datasets
orders = pd.read_csv('orders.csv')
customers = pd.read_csv('customers.csv')
products = pd.read_csv('products.csv')

# Merge datasets
try:
    merged = orders.merge(customers, on='customer_id', how='left')
    merged = merged.merge(products, on='product_id', how='left')
except Exception as e:
    print(f'Merge error: {e}')
    merged = pd.DataFrame()

# Transform
if not merged.empty:
    merged['total'] = merged['quantity'] * merged['price']
    merged['discount'] = np.where(merged['total'] > 100, 0.1, 0)
    merged['final_price'] = merged['total'] * (1 - merged['discount'])

    # Aggregate by customer
    summary = merged.groupby('customer_name').agg(
        total_orders=('order_id', 'count'),
        total_spent=('final_price', 'sum'),
        avg_order=('final_price', 'mean')
    ).reset_index()

    summary = summary.sort_values('total_spent', ascending=False)
    print(summary.head(10).to_string())
""",
        "bad": """import pandas as pd
data = pd.DataFrame({'a': [1,2,3]})
print(data)
""",
    },
    {
        "name": "SQL_subquery_analysis",
        "good": """import sqlite3
import pandas as pd

conn = sqlite3.connect('analytics.db')

# Subquery: customers above average spending
query = '''
    WITH customer_totals AS (
        SELECT customer_id, SUM(amount) as total_spent
        FROM orders
        WHERE order_date >= '2024-01-01'
        GROUP BY customer_id
    )
    SELECT
        c.name,
        c.email,
        ct.total_spent,
        CASE
            WHEN ct.total_spent > 1000 THEN 'Premium'
            WHEN ct.total_spent > 500 THEN 'Regular'
            ELSE 'Basic'
        END as segment
    FROM customers c
    JOIN customer_totals ct ON c.id = ct.customer_id
    WHERE ct.total_spent > (SELECT AVG(total_spent) FROM customer_totals)
    ORDER BY ct.total_spent DESC
'''

try:
    df = pd.read_sql(query, conn)
    # Validate output
    assert 'name' in df.columns, 'Missing name column'
    assert 'segment' in df.columns, 'Missing segment column'
    print(f'Found {len(df)} above-average customers')
    print(df.head(20).to_string())
except Exception as e:
    print(f'Analysis error: {e}')
finally:
    conn.close()
""",
        "bad": """,
""",
    },
]

results = []

for pair in pairs:
    print(f"\n{'='*60}")
    print(f"Pair: {pair['name']}")
    print(f"{'='*60}")
    
    pair_result = {"name": pair["name"], "scores": {}}
    
    for quality, code in [("GOOD", pair["good"]), ("BAD", pair["bad"])]:
        # Create temp solution directory
        sol_dir = Path(tempfile.mkdtemp(prefix=f'{pair["name"]}_{quality}_'))
        (sol_dir / 'solution.py').write_text(code)
        
        try:
            engine = DataScoringEngine(TASK_DIR, sol_dir, WEIGHTS)
            score = engine.evaluate()
            
            s = {
                "correctness": score.correctness,
                "completeness": score.completeness,
                "efficiency": score.efficiency,
                "robustness": score.robustness,
                "clarity": score.clarity,
                "total": score.total,
            }
            pair_result["scores"][quality] = s
            print(f"  {quality}: corr={s['correctness']} comp={s['completeness']} eff={s['efficiency']} rob={s['robustness']} cla={s['clarity']} total={s['total']}")
            
        except Exception as e:
            pair_result["scores"][quality] = {"error": str(e)}
            print(f"  {quality}: ERROR: {e}")
    
    # Calculate delta
    g = pair_result["scores"].get("GOOD", {})
    b = pair_result["scores"].get("BAD", {})
    if "error" not in g and "error" not in b:
        delta = g.get("total", 0) - b.get("total", 0)
        pair_result["delta"] = delta
        pair_result["differentiated"] = delta > 0
        print(f"  DELTA: {delta:.1f} {'✅' if delta > 0 else '❌'}")
    
    results.append(pair_result)

# ── Summary ──
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")

differentiated = sum(1 for r in results if r.get("differentiated"))
total = len(results)
print(f"Differentiated: {differentiated}/{total}")

if differentiated == total:
    print("✅ ALL 5 pairs show differentiation — DataScoringEngine fix verified")
elif differentiated > 0:
    print(f"⚠️ PARTIALLY VERIFIED: {differentiated}/{total} pairs differentiate")
else:
    print("❌ NO differentiation — fix may not be working")

# Save
output_file = Path('risultati/dataengine_verification/results.json').resolve()
output_file.write_text(json.dumps(results, indent=2, default=str), encoding='utf-8')
print(f"\nResults saved to: {output_file}")

# Save script
import shutil as sh
this_file = Path(__file__).resolve()
dest = Path('risultati/dataengine_verification/verify_dataengine.py').resolve()
sh.copy2(str(this_file), str(dest))
print(f"Script saved to: {dest}")
