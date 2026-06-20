from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth as auth_utils
from routers.activities import calculate_step_equivalent

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _require_superuser(current_user: models.User = Depends(auth_utils.get_current_user)) -> models.User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")
    return current_user


@router.get("/conversion-rules", response_model=List[schemas.ConversionRuleResponse])
def get_conversion_rules(
    _: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(models.ConversionRule).order_by(models.ConversionRule.activity_type).all()


@router.post("/conversion-rules", response_model=schemas.ConversionRuleResponse, status_code=201)
def create_conversion_rule(
    body: schemas.ConversionRuleCreate,
    _: models.User = Depends(_require_superuser),
    db: Session = Depends(get_db),
):
    if db.query(models.ConversionRule).filter(
        models.ConversionRule.activity_type == body.activity_type
    ).first():
        raise HTTPException(status_code=409, detail="Activity type already exists")
    rule = models.ConversionRule(
        activity_type=body.activity_type,
        conversion_per_minute=body.conversion_per_minute,
        conversion_per_km=body.conversion_per_km,
        is_default=False,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/conversion-rules/{activity_type}")
def update_conversion_rule(
    activity_type: str,
    body: schemas.ConversionRuleUpdate,
    _: models.User = Depends(_require_superuser),
    db: Session = Depends(get_db),
):
    rule = db.query(models.ConversionRule).filter(
        models.ConversionRule.activity_type == activity_type
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Conversion rule not found")

    if body.conversion_per_minute is not None:
        rule.conversion_per_minute = body.conversion_per_minute
    if body.conversion_per_km is not None:
        rule.conversion_per_km = body.conversion_per_km

    db.flush()

    # Retroactively recalculate all activities of this type
    activities = db.query(models.Activity).filter(
        models.Activity.activity_type == activity_type
    ).all()
    for activity in activities:
        activity.step_equivalent_calculated = calculate_step_equivalent(
            activity.activity_type,
            activity.duration_minutes,
            activity.distance_km,
            activity.manual_steps,
            db,
        )

    db.commit()
    return {"success": True, "message": f"All {activity_type} activities recalculated ({len(activities)} updated)"}


@router.get("/user", response_model=schemas.UserMe)
def get_user_settings(
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    return schemas.UserMe(
        user_id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        is_superuser=current_user.is_superuser,
        weekly_goal=current_user.weekly_goal,
        monthly_goal=current_user.monthly_goal,
    )


@router.put("/user")
def update_user_settings(
    body: schemas.UserSettingsUpdate,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    return {"success": True}
