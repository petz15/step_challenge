from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from database import get_db
import models, schemas, auth as auth_utils

router = APIRouter(prefix="/api/activities", tags=["activities"])


def calculate_step_equivalent(
    activity_type: str,
    duration_minutes: Optional[float],
    distance_km: Optional[float],
    manual_steps: Optional[int],
    db: Session,
) -> int:
    rule = db.query(models.ConversionRule).filter(
        models.ConversionRule.activity_type == activity_type
    ).first()
    multiplier = float(rule.step_multiplier) if rule and rule.step_multiplier is not None else 1.0
    if manual_steps:
        return int(round(manual_steps * multiplier))
    if not rule:
        return 0
    if duration_minutes is not None and duration_minutes > 0:
        return int(round(duration_minutes * rule.conversion_per_minute))
    if distance_km is not None and distance_km > 0:
        return int(round(distance_km * rule.conversion_per_km))
    return 0


@router.post("", response_model=schemas.ActivityResponse, status_code=201)
def create_activity(
    body: schemas.ActivityCreate,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    steps = calculate_step_equivalent(
        body.activity_type, body.duration_minutes, body.distance_km, body.manual_steps, db
    )
    activity = models.Activity(
        user_id=current_user.id,
        activity_type=body.activity_type,
        duration_minutes=body.duration_minutes,
        distance_km=body.distance_km,
        manual_steps=body.manual_steps,
        step_equivalent_calculated=steps,
        date=body.date,
        notes=body.notes,
        source="manual",
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("", response_model=List[schemas.ActivityResponse])
def list_activities(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    user_id: Optional[int] = Query(None),
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(models.Activity)
    target_id = user_id if user_id else current_user.id
    q = q.filter(models.Activity.user_id == target_id)
    if start_date:
        q = q.filter(models.Activity.date >= start_date)
    if end_date:
        q = q.filter(models.Activity.date <= end_date)
    return q.order_by(models.Activity.date.desc(), models.Activity.created_at.desc()).all()


@router.get("/{activity_id}", response_model=schemas.ActivityResponse)
def get_activity(
    activity_id: int,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your activity")
    return activity


@router.put("/{activity_id}", response_model=schemas.ActivityResponse)
def update_activity(
    activity_id: int,
    body: schemas.ActivityUpdate,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your activity")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)

    activity.step_equivalent_calculated = calculate_step_equivalent(
        activity.activity_type,
        activity.duration_minutes,
        activity.distance_km,
        activity.manual_steps,
        db,
    )
    db.commit()
    db.refresh(activity)
    return activity


@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your activity")
    db.delete(activity)
    db.commit()
    return {"success": True}
