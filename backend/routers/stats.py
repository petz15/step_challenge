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


@router.get("/challenge-record")
def get_challenge_record(
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    users = db.query(models.User).all()
    if len(users) < 2:
        return {"users": [], "weekly": {"history": [], "wins": {}, "ties": 0},
                "monthly": {"history": [], "wins": {}, "ties": 0}}

    today = date.today()

    def scores_for(start: date, end: date) -> dict[int, int]:
        base = {u.id: 0 for u in users}
        rows = db.query(
            models.Activity.user_id,
            func.sum(models.Activity.step_equivalent_calculated),
        ).filter(
            models.Activity.date >= start,
            models.Activity.date <= end,
        ).group_by(models.Activity.user_id).all()
        for uid, total in rows:
            base[uid] = int(total or 0)
        return base

    def winner_of(scores: dict[int, int]) -> int | None:
        sorted_ids = sorted(scores, key=lambda k: scores[k], reverse=True)
        if scores[sorted_ids[0]] == scores[sorted_ids[1]]:
            return None
        return sorted_ids[0]

    # Last 12 complete weeks (Mon–Sun), oldest first
    current_monday = today - timedelta(days=today.weekday())
    weekly_history = []
    for i in range(12, 0, -1):
        w_start = current_monday - timedelta(weeks=i)
        w_end = w_start + timedelta(days=6)
        sc = scores_for(w_start, w_end)
        weekly_history.append({
            "period_start": w_start.isoformat(),
            "winner_user_id": winner_of(sc),
            "scores": {str(uid): v for uid, v in sc.items()},
        })

    # Last 12 complete months, oldest first
    y, m = today.year, today.month
    monthly_history = []
    for _ in range(12):
        m -= 1
        if m == 0:
            m, y = 12, y - 1
        m_start = date(y, m, 1)
        m_end = (date(y, m + 1, 1) if m < 12 else date(y + 1, 1, 1)) - timedelta(days=1)
        sc = scores_for(m_start, m_end)
        monthly_history.insert(0, {
            "period_start": m_start.isoformat(),
            "winner_user_id": winner_of(sc),
            "scores": {str(uid): v for uid, v in sc.items()},
        })

    # Tally wins
    wins: dict[str, dict] = {str(u.id): {"weekly": 0, "monthly": 0} for u in users}
    weekly_ties = monthly_ties = 0
    for w in weekly_history:
        wid = w["winner_user_id"]
        if wid is None:
            weekly_ties += 1
        else:
            wins[str(wid)]["weekly"] += 1
    for mo in monthly_history:
        wid = mo["winner_user_id"]
        if wid is None:
            monthly_ties += 1
        else:
            wins[str(wid)]["monthly"] += 1

    return {
        "users": [{"user_id": u.id, "name": u.name} for u in users],
        "weekly": {
            "history": weekly_history,
            "wins": {uid: w["weekly"] for uid, w in wins.items()},
            "ties": weekly_ties,
        },
        "monthly": {
            "history": monthly_history,
            "wins": {uid: w["monthly"] for uid, w in wins.items()},
            "ties": monthly_ties,
        },
    }


@router.get("/health")
def get_health_trends(
    days: int = 14,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    start = date.today() - timedelta(days=days - 1)
    metrics = (
        db.query(models.HealthMetric)
        .filter(
            models.HealthMetric.user_id == current_user.id,
            models.HealthMetric.date >= start,
        )
        .order_by(models.HealthMetric.date)
        .all()
    )

    result: dict[str, list] = {}
    for m in metrics:
        result.setdefault(m.metric_type, []).append(
            {"date": m.date.isoformat(), "value": m.value}
        )
    return result
