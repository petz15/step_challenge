import base64
import hashlib
import os
from datetime import date

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
import auth as auth_utils
from database import get_db
from routers.activities import calculate_step_equivalent

router = APIRouter(prefix="/api/garmin", tags=["garmin"])

# Maps Garmin typeKey → our activity_type from conversion_rules.
# Entries with None are intentionally skipped (no meaningful step equivalent).
GARMIN_TYPE_MAP: dict[str, str | None] = {
    # Running
    "running":                          "Running, Moderate (10 min/mile)",
    "trail_running":                    "Running, Moderate (10 min/mile)",
    "indoor_running":                   "Running, Moderate (10 min/mile)",
    "treadmill_running":                "Running, Moderate (10 min/mile)",
    "virtual_run":                      "Running, Moderate (10 min/mile)",
    "ultra_run":                        "Running, Easy (12 min/mile)",
    # Walking
    "walking":                          "Walking, Moderate",
    "casual_walking":                   "Walking, Slow (2 mph)",
    "speed_walking":                    "Walking, Fast (4 mph)",
    # Hiking
    "hiking":                           "Hiking",
    "mountaineering":                   "Hiking",
    # Cycling
    "cycling":                          "Cycling, Moderate (12 mph)",
    "road_biking":                      "Cycling, Moderate (12 mph)",
    "gravel_cycling":                   "Cycling, Moderate (12 mph)",
    "mountain_biking":                  "Cycling, Vigorous (15 mph)",
    "indoor_cycling":                   "Cycling, Moderate (12 mph)",
    "virtual_ride":                     "Cycling, Moderate (12 mph)",
    "bmx":                              "Cycling, Moderate (12 mph)",
    "recumbent_cycling":                "Cycling, Easy (10 mph)",
    # Swimming
    "swimming":                         "Swimming",
    "open_water_swimming":              "Swimming",
    "pool_swimming":                    "Swimming",
    # Strength & gym
    "strength_training":                "Weight Lifting",
    "fitness_equipment":                "Circuit Training",
    "cardio_training":                  "Circuit Training",
    "hiit":                             "Circuit Training",
    # Yoga & pilates
    "yoga":                             "Yoga",
    "pilates":                          "Pilates",
    # Elliptical & stair
    "elliptical":                       "Elliptical Trainer",
    "stair_climbing":                   "Stair Climbing",
    "floor_climbing":                   "Stair Climbing",
    # Rowing
    "rowing":                           "Rowing",
    "indoor_rowing":                    "Rowing",
    # Water sports
    "kayaking":                         "Kayaking",
    "stand_up_paddleboarding":          "Sailing",
    "canoeing":                         "Canoeing",
    "water_skiing":                     "Water Skiing",
    "surfing":                          "Surfing",
    # Climbing
    "rock_climbing":                    "Rock Climbing",
    "indoor_climbing":                  "Rock Climbing",
    "bouldering":                       "Rock Climbing",
    # Snow
    "skiing":                           "Skiing, Downhill",
    "backcountry_skiing":               "Skiing, Downhill",
    "skate_skiing":                     "Skiing, Cross-Country",
    "cross_country_skiing":             "Skiing, Cross-Country",
    "snowboarding":                     "Snowboarding",
    "snowshoeing":                      "Snowshoeing",
    "sledding":                         "Sledding",
    # Ball sports
    "tennis":                           "Tennis",
    "basketball":                       "Basketball, Game",
    "soccer":                           "Soccer, Recreational",
    "volleyball":                       "Volleyball",
    "squash":                           "Squash",
    "badminton":                        "Badminton, Recreational",
    "rugby":                            "Rugby",
    "golf":                             "Golf, Carrying Clubs",
    # Martial arts & boxing
    "boxing":                           "Boxing, Non-Competitive",
    "kickboxing":                       "Kickboxing",
    "martial_arts":                     "Martial Arts",
    # Skating
    "inline_skating":                   "Rollerblading",
    "ice_skating":                      "Ice Skating, Recreational",
    # Aerobics & dance
    "aerobics":                         "Aerobics, Low Impact",
    "dancing":                          "Dancing",
    "jumpingrope":                      "Jumping Rope, Moderate",
    "jump_rope":                        "Jumping Rope, Moderate",
    # Misc
    "horseback_riding":                 "Horseback Riding",
    "breathwork":                       None,
    "meditation":                       None,
    "other":                            None,
    "generic":                          None,
}

# Garmin provides real step counts for these type keys — use manual_steps instead of conversion.
STEP_ACTIVITY_KEYS = {"running", "trail_running", "indoor_running", "treadmill_running",
                      "virtual_run", "ultra_run", "walking", "casual_walking", "speed_walking",
                      "hiking"}


def _fernet() -> Fernet:
    secret = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def _encrypt(text: str) -> str:
    return _fernet().encrypt(text.encode()).decode()


def _decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


def _garmin_client(email: str, password: str):
    """Authenticate with Garmin Connect and return a logged-in client."""
    try:
        import garminconnect
    except ImportError:
        raise HTTPException(status_code=500, detail="garminconnect library not installed")

    try:
        client = garminconnect.Garmin(email, password)
        client.login()
        return client
    except garminconnect.GarminConnectAuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Garmin authentication failed: {exc}. "
                   "Check credentials or disable 2FA on your Garmin Connect account.",
        )
    except garminconnect.GarminConnectTooManyRequestsError:
        raise HTTPException(status_code=429, detail="Garmin Connect rate limit reached. Try again later.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Garmin Connect: {exc}")


@router.post("/connect", response_model=schemas.GarminStatusResponse)
def garmin_connect(
    body: schemas.GarminConnectRequest,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    """Save Garmin credentials after verifying they work."""
    _garmin_client(body.email, body.password)  # raises on bad creds
    current_user.garmin_email = body.email
    current_user.garmin_password_enc = _encrypt(body.password)
    db.commit()
    return schemas.GarminStatusResponse(connected=True, email=body.email)


@router.get("/status", response_model=schemas.GarminStatusResponse)
def garmin_status(current_user: models.User = Depends(auth_utils.get_current_user)):
    return schemas.GarminStatusResponse(
        connected=current_user.garmin_password_enc is not None,
        email=current_user.garmin_email,
    )


@router.post("/sync", response_model=schemas.GarminSyncResponse)
def garmin_sync(
    body: schemas.GarminSyncRequest,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    """Import activities from Garmin Connect for the given date range."""
    if not current_user.garmin_password_enc:
        raise HTTPException(status_code=400, detail="Garmin not connected. Go to Settings → Garmin Sync to connect.")

    if body.start_date > body.end_date:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")

    password = _decrypt(current_user.garmin_password_enc)
    client = _garmin_client(current_user.garmin_email, password)

    try:
        raw_activities = client.get_activities_by_date(
            startdate=body.start_date.strftime("%Y-%m-%d"),
            enddate=body.end_date.strftime("%Y-%m-%d"),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch activities from Garmin: {exc}")

    imported = 0
    skipped = 0

    for act in raw_activities:
        garmin_id = str(act.get("activityId", ""))
        if not garmin_id:
            skipped += 1
            continue

        # Skip already-imported activities
        exists = db.query(models.Activity).filter(
            models.Activity.garmin_activity_id == garmin_id,
            models.Activity.user_id == current_user.id,
        ).first()
        if exists:
            skipped += 1
            continue

        # Map Garmin activity type to ours
        type_key = (act.get("activityType") or {}).get("typeKey", "").lower()
        our_type = GARMIN_TYPE_MAP.get(type_key)
        if our_type is None:
            skipped += 1
            continue

        # Parse date from startTimeLocal ("2026-06-20 07:30:00" or "2026-06-20T07:30:00")
        start_str = act.get("startTimeLocal", "")
        try:
            activity_date = date.fromisoformat(start_str[:10])
        except (ValueError, TypeError):
            skipped += 1
            continue

        # Parse duration / distance / steps
        duration_s = act.get("duration") or 0
        duration_min = round(duration_s / 60, 1) if duration_s > 0 else None
        distance_m = act.get("distance") or 0
        distance_km = round(distance_m / 1000, 3) if distance_m > 0 else None
        garmin_steps = act.get("steps") or 0

        # Use real step count for step-based activities; duration/distance otherwise
        if garmin_steps > 0 and type_key in STEP_ACTIVITY_KEYS:
            manual_steps = int(garmin_steps)
            duration_min = None
            distance_km = None
        else:
            manual_steps = None

        steps = calculate_step_equivalent(our_type, duration_min, distance_km, manual_steps, db)

        activity_name = act.get("activityName") or ""

        db.add(models.Activity(
            user_id=current_user.id,
            activity_type=our_type,
            duration_minutes=duration_min,
            distance_km=distance_km,
            manual_steps=manual_steps,
            step_equivalent_calculated=steps,
            date=activity_date,
            notes=activity_name if activity_name else None,
            source="garmin_api",
            garmin_activity_id=garmin_id,
        ))
        imported += 1

    db.commit()
    return schemas.GarminSyncResponse(imported=imported, skipped=skipped)


@router.delete("/disconnect")
def garmin_disconnect(
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    current_user.garmin_email = None
    current_user.garmin_password_enc = None
    db.commit()
    return {"success": True}
