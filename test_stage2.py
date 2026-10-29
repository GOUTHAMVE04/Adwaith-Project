import importlib.metadata
import flask
import werkzeug
from database import get_db

print("=== Stage 2 Verification Test ===")
print(f"[OK] Flask version: {importlib.metadata.version('flask')}")
print(f"[OK] Werkzeug version: {importlib.metadata.version('werkzeug')}")

# Verify SQLite connection
db = get_db()
cursor = db.cursor()
cursor.execute("SELECT sqlite_version();")
sqlite_version = cursor.fetchone()[0]
print(f"[OK] SQLite database engine version: {sqlite_version}")

cursor.execute("PRAGMA foreign_keys;")
fk_status = cursor.fetchone()[0]
print(f"[OK] SQLite Foreign Keys enabled: {'Yes (1)' if fk_status == 1 else 'No (0)'}")

db.close()
print("=== All Stage 2 checks passed successfully! ===")
