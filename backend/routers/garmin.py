import base64
import hashlib
import json
import os
import tempfile
from datetime import date, timedelta

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
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
    "running":                          "Running, Moderate (10 km/h)",
    "trail_running":                    "Running, Moderate (10 km/h)",
    "indoor_running":                   "Running, Moderate (10 km/h)",
    "treadmill_running":                "Running, Moderate (10 km/h)",
    "virtual_run":                      "Running, Moderate (10 km/h)",
    "ultra_run":                        "Running, Easy (8 km/h)",
    # Walking
    "walking":                          "Walking, Moderate",
    "casual_walking":                   "Walking, Slow (3 km/h)",
    "speed_walking":                    "Walking, Fast (6 km/h)",
    # Hiking
    "hiking":                           "Hiking",
    "mountaineering":                   "Hiking",
    # Cycling
    "cycling":                          "Cycling, Moderate (19 km/h)",
    "road_biking":                      "Cycling, Moderate (19 km/h)",
    "gravel_cycling":                   "Cycling, Moderate (19 km/h)",
    "mountain_biking":                  "Cycling, Vigorous (24 km/h)",
    "indoor_cycling":                   "Cycling, Moderate (19 km/h)",
    "virtual_ride":                     "Cycling, Moderate (19 km/h)",
    "bmx":                              "Cycling, Moderate (19 km/h)",
    "recumbent_cycling":                "Cycling, Easy (16 km/h)",
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


def _upsert_health_metric(
    db: Session, user_id: int, day: date, metric_type: str, value: float
) -> None:
    existing = (
        db.query(models.HealthMetric)
        .filter(
            models.HealthMetric.user_id == user_id,
            models.HealthMetric.date == day,
            models.HealthMetric.metric_type == metric_type,
        )
        .first()
    )
    if existing:
        existing.value = value
    else:
        db.add(models.HealthMetric(
            user_id=user_id,
            date=day,
            metric_type=metric_type,
            value=value,
            source="garmin_api",
        ))


def _fernet() -> Fernet:
    secret = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def _encrypt(text: str) -> str:
    return _fernet().encrypt(text.encode()).decode()


def _decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


class _MfaRequiredError(Exception):
    """Raised from the prompt_mfa callback when no code was supplied yet."""


def _dump_tokens(client) -> str:
    """Serialize garth session tokens to an encrypted-ready JSON string."""
    with tempfile.TemporaryDirectory() as tmpdir:
        client.garth.dump(tmpdir)
        files = {}
        for fname in os.listdir(tmpdir):
            with open(os.path.join(tmpdir, fname)) as f:
                files[fname] = f.read()
        return json.dumps(files)


def _garmin_client_from_tokens(encrypted_tokens: str) -> object:
    """Restore a Garmin client from stored session tokens (no MFA needed)."""
    try:
        import garminconnect
    except ImportError:
        raise HTTPException(status_code=500, detail="garminconnect library not installed")

    files = json.loads(_decrypt(encrypted_tokens))
    with tempfile.TemporaryDirectory() as tmpdir:
        for fname, content in files.items():
            with open(os.path.join(tmpdir, fname), "w") as f:
                f.write(content)
        client = garminconnect.Garmin()
        client.login(tmpdir)
    return client


def _garmin_fresh_login(email: str, password: str, mfa_code: str | None = None) -> object:
    """Full credential login with optional MFA.

    If Garmin requests MFA and no code was provided, raises HTTP 400 "mfa_required"
    so the frontend can show the code input and resubmit.
    """
    try:
        import garminconnect
    except ImportError:
        raise HTTPException(status_code=500, detail="garminconnect library not installed")

    def _prompt_mfa() -> str:
        if mfa_code:
            return mfa_code
        raise _MfaRequiredError()

    try:
        client = garminconnect.Garmin(email, password, prompt_mfa=_prompt_mfa)
        client.login()
        return client
    except _MfaRequiredError:
        raise HTTPException(status_code=400, detail="mfa_required")
    except garminconnect.GarminConnectAuthenticationError as exc:
        raise HTTPException(status_code=401, detail=f"Garmin authentication failed: {exc}")
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
    """Full credential login — saves OAuth tokens so future syncs skip re-authentication."""
    client = _garmin_fresh_login(body.email, body.password, body.mfa_code)
    current_user.garmin_email = body.email
    current_user.garmin_password_enc = _encrypt(body.password)
    current_user.garmin_tokens_enc = _encrypt(_dump_tokens(client))
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
    """Import Garmin activities and net passive daily steps for the given date range."""
    if not current_user.garmin_email:
        raise HTTPException(status_code=400, detail="Garmin not connected. Go to Settings → Garmin Sync to connect.")

    if body.start_date > body.end_date:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")

    # Prefer stored session tokens — no MFA needed, no password re-send.
    # Fall back to password re-login (for accounts without MFA or for first sync after migration).
    client = None
    if current_user.garmin_tokens_enc:
        try:
            client = _garmin_client_from_tokens(current_user.garmin_tokens_enc)
        except Exception:
            client = None  # tokens expired — try password below

    if client is None:
        if not current_user.garmin_password_enc:
            raise HTTPException(
                status_code=400,
                detail="Garmin session expired. Go to Settings → Garmin Sync to reconnect.",
            )
        password = _decrypt(current_user.garmin_password_enc)
        client = _garmin_fresh_login(current_user.garmin_email, password)
        try:
            current_user.garmin_tokens_enc = _encrypt(_dump_tokens(client))
            db.commit()
        except Exception:
            pass

    start_str = body.start_date.strftime("%Y-%m-%d")
    end_str = body.end_date.strftime("%Y-%m-%d")

    try:
        raw_activities = client.get_activities_by_date(startdate=start_str, enddate=end_str)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch activities from Garmin: {exc}")

    imported = 0
    skipped = 0
    warnings: list[str] = []

    for act in raw_activities:
        garmin_id = str(act.get("activityId", ""))
        if not garmin_id:
            skipped += 1
            continue

        type_key = (act.get("activityType") or {}).get("typeKey", "").lower()
        our_type = GARMIN_TYPE_MAP.get(type_key)
        if our_type is None:
            skipped += 1
            continue

        start_time_str = act.get("startTimeLocal", "")
        try:
            activity_date = date.fromisoformat(start_time_str[:10])
        except (ValueError, TypeError):
            skipped += 1
            continue

        duration_s = act.get("duration") or 0
        duration_min = round(duration_s / 60, 1) if duration_s > 0 else None
        distance_m = act.get("distance") or 0
        distance_km = round(distance_m / 1000, 3) if distance_m > 0 else None
        garmin_steps = act.get("steps") or 0

        # Check if already imported; if so, recalculate only if it has 0 steps
        # (can happen when a type-name mismatch previously caused conversion to fail)
        exists = db.query(models.Activity).filter(
            models.Activity.garmin_activity_id == garmin_id,
            models.Activity.user_id == current_user.id,
        ).first()
        if exists:
            if exists.step_equivalent_calculated == 0 and exists.manual_steps is None:
                conv_dur = duration_min if type_key not in STEP_ACTIVITY_KEYS else None
                conv_dist = distance_km if type_key not in STEP_ACTIVITY_KEYS else None
                new_steps = calculate_step_equivalent(our_type, conv_dur, conv_dist, None, db)
                if new_steps > 0:
                    exists.step_equivalent_calculated = new_steps
                    imported += 1
                    continue
            skipped += 1
            continue

        # Step-based activities (running, walking, hiking): use Garmin's real step count.
        # Everything else (cycling, strength, etc.): convert via duration/distance rules.
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

    # Flush so the new activities are visible to the step-deduction query below.
    db.flush()

    # --- Daily passive steps ---
    # Garmin's daily total includes steps from tracked workouts (running, walking, hiking).
    # We subtract those to get only the passive steps (errands, walking around, etc.)
    # and upsert one "Manual Steps" entry per day so re-syncing mid-day updates the count.
    steps_updated = 0
    try:
        daily_steps_data = client.get_daily_steps(start_str, end_str)
    except Exception as exc:
        daily_steps_data = []
        warnings.append(f"Could not fetch daily step totals from Garmin Connect: {exc}")

    for day_data in (daily_steps_data or []):
        day_str = day_data.get("calendarDate", "")
        total_steps = day_data.get("totalSteps") or 0
        if not day_str or total_steps <= 0:
            continue

        try:
            day_date = date.fromisoformat(day_str)
        except ValueError:
            continue

        # Sum of real Garmin step counts already stored for this user on this day
        # (i.e., activities where we used manual_steps from Garmin, not converted ones).
        activity_steps: int = db.query(func.coalesce(func.sum(models.Activity.manual_steps), 0)).filter(
            models.Activity.user_id == current_user.id,
            models.Activity.date == day_date,
            models.Activity.source == "garmin_api",
            models.Activity.garmin_activity_id.notlike("daily_steps_%"),
            models.Activity.manual_steps.isnot(None),
        ).scalar() or 0

        net_passive = int(total_steps) - int(activity_steps)
        if net_passive <= 0:
            continue

        synthetic_id = f"daily_steps_{day_str}"
        existing = db.query(models.Activity).filter(
            models.Activity.garmin_activity_id == synthetic_id,
            models.Activity.user_id == current_user.id,
        ).first()

        if existing:
            existing.manual_steps = net_passive
            existing.step_equivalent_calculated = net_passive
        else:
            db.add(models.Activity(
                user_id=current_user.id,
                activity_type="Manual Steps",
                manual_steps=net_passive,
                step_equivalent_calculated=net_passive,
                date=day_date,
                notes="Passive daily steps",
                source="garmin_api",
                garmin_activity_id=synthetic_id,
            ))
        steps_updated += 1

    # --- Health data (resting HR, sleep) ---
    # Cap to 7 days to keep the sync fast; focus on recent/missing data.
    health_synced = 0
    health_end = min(body.end_date, date.today())
    health_start = max(body.start_date, health_end - timedelta(days=6))
    current_day = health_start
    while current_day <= health_end:
        day_str = current_day.isoformat()

        # Resting heart rate (from daily heart rate summary)
        try:
            hr_data = client.get_heart_rates(day_str)
            if isinstance(hr_data, dict):
                rhr = hr_data.get("restingHeartRate")
                if rhr and int(rhr) > 20:
                    _upsert_health_metric(db, current_user.id, current_day, "resting_hr", float(rhr))
                    health_synced += 1
        except Exception:
            pass

        # Sleep duration
        try:
            sleep_resp = client.get_sleep_data(day_str)
            if isinstance(sleep_resp, dict):
                dto = sleep_resp.get("dailySleepDTO") or {}
                sleep_secs = dto.get("sleepTimeSeconds") or 0
                if sleep_secs >= 3600:
                    _upsert_health_metric(
                        db, current_user.id, current_day, "sleep_hours",
                        round(sleep_secs / 3600, 1),
                    )
                    health_synced += 1
                # Sleep score (0-100 if available)
                scores = dto.get("sleepScores") or {}
                if isinstance(scores, dict):
                    overall = scores.get("overall") or {}
                    score_val = overall.get("value") if isinstance(overall, dict) else overall
                    if score_val and int(score_val) > 0:
                        _upsert_health_metric(
                            db, current_user.id, current_day, "sleep_score", float(score_val)
                        )
        except Exception:
            pass

        current_day += timedelta(days=1)

    db.commit()
    return schemas.GarminSyncResponse(
        imported=imported,
        skipped=skipped,
        steps_updated=steps_updated,
        health_synced=health_synced,
        warnings=warnings,
    )


@router.delete("/disconnect")
def garmin_disconnect(
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(get_db),
):
    current_user.garmin_email = None
    current_user.garmin_password_enc = None
    current_user.garmin_tokens_enc = None
    db.commit()
    return {"success": True}
