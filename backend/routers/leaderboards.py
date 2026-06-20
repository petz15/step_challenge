from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import date, timedelta
from database import get_db
import models, schemas, auth as auth_utils

router = APIRouter(prefix="/api/leaderboards", tags=["leaderboards"])


def _build_leaderboard(
    db: Session, start: date, end: date, period_type: str
) -> List[schemas.LeaderboardEntry]:
    rows = (
        db.query(
            models.Activity.user_id,
            func.sum(models.Activity.step_equivalent_calculated).label("total"),
        )
        .filter(models.Activity.date >= start, models.Activity.date <= end)
        .group_by(models.Activity.user_id)
        .order_by(func.sum(models.Activity.step_equivalent_calculated).desc())
        .all()
    )

    # All users should appear even with zero steps
    all_users = db.query(models.User).all()
    user_totals = {row.user_id: row.total for row in rows}
    for u in all_users:
        if u.id not in user_totals:
            user_totals[u.id] = 0

    sorted_users = sorted(all_users, key=lambda u: user_totals.get(u.id, 0), reverse=True)

    entries = []
    for rank, user in enumerate(sorted_users, start=1):
        total = user_totals.get(user.id, 0)
        goal = user.weekly_goal if period_type == "weekly" else user.monthly_goal if period_type == "monthly" else None
        goal_progress = round((total / goal) * 100, 1) if goal and goal > 0 else None
        entries.append(
            schemas.LeaderboardEntry(
                rank=rank,
                user_id=user.id,
                name=user.name,
                total_steps=total,
                goal=goal,
                goal_progress=goal_progress,
            )
        )
    return entries


@router.get("/daily", response_model=List[schemas.LeaderboardEntry])
def daily_leaderboard(
    date_param: Optional[date] = Query(None, alias="date"),
    _: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    day = date_param or date.today()
    return _build_leaderboard(db, day, day, "daily")


@router.get("/weekly", response_model=List[schemas.LeaderboardEntry])
def weekly_leaderboard(
    week_start: Optional[date] = Query(None),
    _: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    if week_start:
        start = week_start
    else:
        today = date.today()
        start = today - timedelta(days=today.weekday())  # Monday
    end = start + timedelta(days=6)
    return _build_leaderboard(db, start, end, "weekly")


@router.get("/monthly", response_model=List[schemas.LeaderboardEntry])
def monthly_leaderboard(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    _: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    start = date(y, m, 1)
    # last day of month
    if m == 12:
        end = date(y + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(y, m + 1, 1) - timedelta(days=1)
    return _build_leaderboard(db, start, end, "monthly")
