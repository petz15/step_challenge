from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
import models
import auth as auth_utils

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _get_streak(user_id: int, db: Session) -> int:
    activity_dates = set(
        d[0] for d in db.query(models.Activity.date)
        .filter(models.Activity.user_id == user_id)
        .distinct().all()
    )
    if not activity_dates:
        return 0
    today = date.today()
    check = today if today in activity_dates else today - timedelta(days=1)
    if check not in activity_dates:
        return 0
    streak = 0
    while check in activity_dates:
        streak += 1
        check -= timedelta(days=1)
    return streak


@router.get("/overview")
def get_overview(
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    users = db.query(models.User).all()

    streaks = [
        {"user_id": u.id, "name": u.name, "streak": _get_streak(u.id, db)}
        for u in users
    ]

    today = date.today()
    current_monday = today - timedelta(days=today.weekday())

    weekly_trend = []
    for i in range(7, -1, -1):
        week_start = current_monday - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        rows = db.query(
            models.Activity.user_id,
            func.sum(models.Activity.step_equivalent_calculated),
        ).filter(
            models.Activity.date >= week_start,
            models.Activity.date <= week_end,
        ).group_by(models.Activity.user_id).all()

        weekly_trend.append({
            "week_start": week_start.isoformat(),
            "totals": {str(uid): int(steps or 0) for uid, steps in rows},
        })

    return {"streaks": streaks, "weekly_trend": weekly_trend}
