import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.database.connection import dispose_engine, engine


async def main() -> None:
    async with engine.begin() as connection:
        table_check = await connection.execute(
            text("SELECT to_regclass('public.data_original') AS table_name")
        )
        table_name = table_check.scalar_one_or_none()
        if table_name is None:
            raise RuntimeError("Table public.data_original was not found.")

        count_result = await connection.execute(text("SELECT COUNT(*) FROM data_original"))
        total_records = int(count_result.scalar_one() or 0)
    await dispose_engine()
    print("Database read-only check successful.")
    print(f"Table: {table_name}")
    print(f"Total records in data_original: {total_records}")


if __name__ == "__main__":
    asyncio.run(main())