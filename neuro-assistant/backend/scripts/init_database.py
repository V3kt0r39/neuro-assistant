import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.database.connection import create_db_tables, dispose_engine


async def main() -> None:
    await create_db_tables()
    await dispose_engine()
    print("Database tables were created successfully.")


if __name__ == "__main__":
    asyncio.run(main())