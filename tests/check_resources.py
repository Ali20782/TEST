import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Check actual resource values in database
cur.execute("""
    SELECT DISTINCT resource, COUNT(*) as count
    FROM event_logs
    WHERE case_id IN ('173688', '173691', '173694')
    GROUP BY resource
    ORDER BY count DESC
    LIMIT 20
""")

print("Actual resource values in database:")
for row in cur.fetchall():
    print(f"  '{row[0]}' -> {row[1]} events")

# Check if resource is stored with extra whitespace or formatting
cur.execute("""
    SELECT case_id, resource, activity
    FROM event_logs
    WHERE case_id = '173688'
    LIMIT 5
""")

print("\nSample data from case 173688:")
for row in cur.fetchall():
    print(f"  Case: {row[0]}, Resource: '{row[1]}' (type: {type(row[1])}), Activity: {row[2]}")

conn.close()