import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import init_db, engine
from sqlalchemy import inspect

init_db()

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\n=== 数据库中的表 ===")
for table in tables:
    print(f"\n表名: {table}")
    for col in inspector.get_columns(table):
        print(f"  - {col['name']} ({col['type']})")