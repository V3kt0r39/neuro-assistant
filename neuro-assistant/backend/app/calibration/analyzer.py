from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import EEGRecord, EmotionThreshold


async def calculate_and_store_thresholds(session: AsyncSession) -> list[EmotionThreshold]:
    stats_query = (
        select(
            EEGRecord.self_reported_emotion.label("emotion"),
            func.avg(EEGRecord.concentration).label("conc_avg"),
            func.avg(EEGRecord.relaxation).label("relax_avg"),
            func.min(EEGRecord.concentration).label("conc_min"),
            func.max(EEGRecord.concentration).label("conc_max"),
            func.min(EEGRecord.relaxation).label("relax_min"),
            func.max(EEGRecord.relaxation).label("relax_max"),
            func.count(EEGRecord.id).label("sample_count"),
        )
        .group_by(EEGRecord.self_reported_emotion)
        .order_by(EEGRecord.self_reported_emotion.asc())
    )

    aggregated_rows = (await session.execute(stats_query)).mappings().all()
    if not aggregated_rows:
        raise ValueError("No calibration EEG records found. Add data through /api/calibrate first.")

    existing_thresholds = {
        threshold.emotion: threshold
        for threshold in (await session.execute(select(EmotionThreshold))).scalars().all()
    }

    updated_thresholds: list[EmotionThreshold] = []
    for row in aggregated_rows:
        emotion = str(row["emotion"])
        threshold = existing_thresholds.get(emotion)
        if threshold is None:
            threshold = EmotionThreshold(emotion=emotion)
            session.add(threshold)

        threshold.conc_avg = float(row["conc_avg"])
        threshold.relax_avg = float(row["relax_avg"])
        threshold.conc_min = float(row["conc_min"])
        threshold.conc_max = float(row["conc_max"])
        threshold.relax_min = float(row["relax_min"])
        threshold.relax_max = float(row["relax_max"])
        threshold.sample_count = int(row["sample_count"])
        updated_thresholds.append(threshold)

    await session.commit()
    for threshold in updated_thresholds:
        await session.refresh(threshold)

    return updated_thresholds


async def get_thresholds(session: AsyncSession) -> list[EmotionThreshold]:
    thresholds_query = select(EmotionThreshold).order_by(EmotionThreshold.emotion.asc())
    return list((await session.execute(thresholds_query)).scalars().all())