"""Check database tables and schema"""
import asyncio
from sqlalchemy import inspect, text
from app.core.database import async_engine, sync_engine

async def check_tables():
    print("Checking database tables...")
    
    # Use sync engine for inspection
    inspector = inspect(sync_engine)
    tables = inspector.get_table_names()
    
    print(f"\n✅ Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")
        columns = inspector.get_columns(table)
        print(f"    Columns: {len(columns)}")
        for col in columns[:5]:  # Show first 5 columns
            print(f"      • {col['name']} ({col['type']})")
        if len(columns) > 5:
            print(f"      ... and {len(columns) - 5} more")
    
    if not tables:
        print("\n❌ No tables found! Database needs to be initialized.")
    
    # Try to connect
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"\n✅ Database connection: OK")
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_tables())
