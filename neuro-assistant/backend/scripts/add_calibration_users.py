import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.database.connection import AsyncSessionLocal, dispose_engine
from app.database.models import EEGRecord, User

CALIBRATION_RAW_DATA: dict[str, list[tuple[float, float, str]]] = {
    "Andrey": [(41, 35, "SAD"), (78, 15, "HAPPY"), (10, 78, "CALM")],
    "Kirill": [(37, 32, "SAD"), (70, 20, "HAPPY"), (12, 72, "CALM")],
    "Dany": [(48, 39, "SAD"), (83, 7, "HAPPY"), (15, 80, "CALM")],
    "Ivan": [(36, 34, "SAD"), (80, 18, "HAPPY"), (17, 74, "CALM")],
}


async def seed_calibration_users(include_samples: bool = False) -> tuple[int, int]:
    created_users = 0
    created_records = 0

    async with AsyncSessionLocal() as session:
        for name, records in CALIBRATION_RAW_DATA.items():
            user = await session.scalar(select(User).where(User.name == name))
            if user is None:
                user = User(name=name, is_calibration_user=True)
                session.add(user)
                await session.flush()
                created_users += 1
            elif not user.is_calibration_user:
                user.is_calibration_user = True

            if not include_samples:
                continue

            for concentration, relaxation, emotion in records:
                existing_record_id = await session.scalar(
                    select(EEGRecord.id).where(
                        EEGRecord.user_id == user.id,
                        EEGRecord.concentration == concentration,
                        EEGRecord.relaxation == relaxation,
                        EEGRecord.self_reported_emotion == emotion,
                    )
                )
                if existing_record_id is None:
                    session.add(
                        EEGRecord(
                            user_id=user.id,
                            concentration=concentration,
                            relaxation=relaxation,
                            self_reported_emotion=emotion,
                        )
                    )
                    created_records += 1

        await session.commit()

    return created_users, created_records


async def main(include_samples: bool) -> None:
    created_users, created_records = await seed_calibration_users(include_samples=include_samples)
    print(f"Calibration users created: {created_users}")
    if include_samples:
        print(f"Calibration EEG samples created: {created_records}")
    else:
        print("Raw EEG samples were not added (use --include-samples to seed them).")
    await dispose_engine()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed calibration users and optionally raw EEG data.")
    parser.add_argument(
        "--include-samples",
        action="store_true",
        help="Also add 12 calibration EEG records from the specification.",
    )
    args = parser.parse_args()

    asyncio.run(main(include_samples=args.include_samples))
