"""
app/services/wearables/normaliser.py

Converts raw Fitbit API responses into flat, stable dicts
for storage in health_metrics.data (JSONB).

Each normalise_* returns a dict with consistent keys the
trend detector and agents can rely on.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def normalise_sleep(raw: dict[str, Any]) -> dict[str, Any] | None:
    """
    Normalise /1.2/user/-/sleep/date/{date}.json

    Returns None when no sleep log exists for that date.
    Picks isMainSleep=True entry, falls back to longest duration.
    """
    entries = raw.get("sleep", [])
    if not entries:
        return None

    main = next((s for s in entries if s.get("isMainSleep")), None)
    if main is None:
        main = max(entries, key=lambda s: s.get("duration", 0))

    summary = raw.get("summary", {})
    stages = main.get("levels", {}).get("summary", {})

    return {
        "duration_ms": main.get("duration", 0),
        "minutes_asleep": main.get("minutesAsleep", 0),
        "minutes_awake": main.get("minutesAwake", 0),
        "minutes_in_bed": main.get("timeInBed", 0),
        "efficiency": main.get("efficiency", 0),
        "start_time": main.get("startTime"),
        "end_time": main.get("endTime"),
        "stages": {
            "deep_minutes": stages.get("deep", {}).get("minutes", 0),
            "light_minutes": stages.get("light", {}).get("minutes", 0),
            "rem_minutes": stages.get("rem", {}).get("minutes", 0),
            "wake_minutes": stages.get("wake", {}).get("minutes", 0),
        },
        "total_minutes_asleep": summary.get("totalMinutesAsleep", main.get("minutesAsleep", 0)),
        "total_time_in_bed": summary.get("totalTimeInBed", main.get("timeInBed", 0)),
    }


def normalise_activity(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Normalise /1/user/-/activities/date/{date}.json"""
    s = raw.get("summary")
    if not s:
        return None

    distances = s.get("distances", [])
    total_km = next((d["distance"] for d in distances if d.get("activity") == "total"), 0.0)

    lightly = s.get("lightlyActiveMinutes", 0)
    fairly = s.get("fairlyActiveMinutes", 0)
    very = s.get("veryActiveMinutes", 0)

    return {
        "steps": s.get("steps", 0),
        "calories_out": s.get("caloriesOut", 0),
        "sedentary_minutes": s.get("sedentaryMinutes", 0),
        "lightly_active_minutes": lightly,
        "fairly_active_minutes": fairly,
        "very_active_minutes": very,
        "total_active_minutes": lightly + fairly + very,
        "distance_km": total_km,
        "floors": s.get("floors", 0),
    }


def normalise_heart_rate(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Normalise /1/user/-/activities/heart/date/{date}/1d.json"""
    entries = raw.get("activities-heart", [])
    if not entries:
        return None

    value = entries[0].get("value", {})
    zones = {
        z["name"].lower().replace(" ", "_"): z.get("minutes", 0)
        for z in value.get("heartRateZones", [])
    }

    return {
        "resting_heart_rate": value.get("restingHeartRate"),
        "zones": {
            "out_of_range_minutes": zones.get("out_of_range", 0),
            "fat_burn_minutes": zones.get("fat_burn", 0),
            "cardio_minutes": zones.get("cardio", 0),
            "peak_minutes": zones.get("peak", 0),
        },
    }
