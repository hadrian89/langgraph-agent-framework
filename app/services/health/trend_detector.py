"""
app/services/health/trend_detector.py

Analyses stored health_metrics and surfaces structured TrendReport
objects for injection into agent context.

Sync implementation — matches your SessionLocal/get_db pattern.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.health_repository import HealthRepository

logger = logging.getLogger(__name__)

# ── Thresholds ──────────────────────────────────────────────────────────────
SLEEP_POOR_HOURS = 6.0
SLEEP_POOR_STREAK = 3
SLEEP_OPTIMAL_MIN = 7.0
SLEEP_OPTIMAL_MAX = 9.0
SLEEP_LOW_DEEP_MINUTES = 45

STEPS_SEDENTARY = 5000
STEPS_SEDENTARY_STREAK = 3
STEPS_GOAL = 10_000
ACTIVE_MINUTES_GOAL = 30

RHR_CRITICAL = 100
RHR_ELEVATED = 80
CARDIO_PEAK_OVERTRAINING = 90


# ── Result types ────────────────────────────────────────────────────────────


@dataclass
class TrendAlert:
    category: str  # sleep | activity | heart_rate
    severity: str  # info | warning | critical
    key: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendReport:
    user_id: str
    generated_at: date
    alerts: list[TrendAlert] = field(default_factory=list)
    summaries: dict[str, Any] = field(default_factory=dict)

    def has_alerts(self) -> bool:
        return bool(self.alerts)

    def to_agent_context(self) -> str:
        """Compact block injected into the insight agent system prompt."""
        if not self.alerts and not self.summaries:
            return "No significant health trends detected in the last 7 days."

        lines = ["## Health trend summary\n"]
        if self.summaries:
            lines.append("### Recent averages (last 7 days)")
            for k, v in self.summaries.items():
                lines.append(f"- {k.replace('_', ' ')}: {v}")
            lines.append("")
        if self.alerts:
            icons = {"info": "ℹ", "warning": "⚠", "critical": "🚨"}
            lines.append("### Detected trends")
            for a in self.alerts:
                lines.append(f"{icons.get(a.severity, '•')} [{a.category}] {a.message}")
        return "\n".join(lines)


# ── Main entry point ────────────────────────────────────────────────────────


def build_trend_report(
    user_id: str,
    db: Session,
    lookback_days: int = 7,
) -> TrendReport:
    """
    Load recent metrics from DB and return a populated TrendReport.
    Call from insight_agent before invoking the LLM.
    """
    repo = HealthRepository(db)
    report = TrendReport(user_id=user_id, generated_at=date.today())

    _analyse_sleep(repo.get_metrics(user_id, "sleep", days=lookback_days), report)
    _analyse_activity(repo.get_metrics(user_id, "activity", days=lookback_days), report)
    _analyse_heart_rate(repo.get_metrics(user_id, "heart_rate", days=lookback_days), report)

    return report


# ── Sleep ────────────────────────────────────────────────────────────────────


def _analyse_sleep(rows: list[Any], report: TrendReport) -> None:
    if not rows:
        return
    hours_list = [r.data.get("minutes_asleep", 0) / 60 for r in rows]
    avg_hours = sum(hours_list) / len(hours_list)
    avg_eff = sum(r.data.get("efficiency", 0) for r in rows) / len(rows)

    report.summaries["avg_sleep_hours"] = f"{avg_hours:.1f}h"
    report.summaries["avg_sleep_efficiency"] = f"{avg_eff:.0f}%"

    streak = _trailing_streak([h < SLEEP_POOR_HOURS for h in hours_list])
    if streak >= SLEEP_POOR_STREAK:
        report.alerts.append(
            TrendAlert(
                category="sleep",
                severity="warning",
                key="sleep_deficit_streak",
                message=(
                    f"Sleep below {SLEEP_POOR_HOURS:.0f}h for {streak} consecutive nights "
                    f"(avg {avg_hours:.1f}h). Consider an earlier bedtime tonight."
                ),
                data={"streak_days": streak, "avg_hours": round(avg_hours, 1)},
            )
        )
    elif avg_hours < SLEEP_POOR_HOURS:
        report.alerts.append(
            TrendAlert(
                category="sleep",
                severity="info",
                key="sleep_below_threshold",
                message=(
                    f"Average sleep this week is {avg_hours:.1f}h, "
                    f"below the recommended {SLEEP_OPTIMAL_MIN:.0f}–{SLEEP_OPTIMAL_MAX:.0f}h."
                ),
                data={"avg_hours": round(avg_hours, 1)},
            )
        )

    avg_deep = sum(r.data.get("stages", {}).get("deep_minutes", 0) for r in rows) / len(rows)
    if avg_deep < SLEEP_LOW_DEEP_MINUTES:
        report.alerts.append(
            TrendAlert(
                category="sleep",
                severity="info",
                key="low_deep_sleep",
                message=(
                    f"Average deep sleep is {avg_deep:.0f} min/night. "
                    "Reducing caffeine after 14:00 and screen time before bed can help."
                ),
                data={"avg_deep_minutes": round(avg_deep)},
            )
        )


# ── Activity ─────────────────────────────────────────────────────────────────


def _analyse_activity(rows: list[Any], report: TrendReport) -> None:
    if not rows:
        return
    steps_list = [r.data.get("steps", 0) for r in rows]
    avg_steps = sum(steps_list) / len(steps_list)
    avg_active = sum(r.data.get("total_active_minutes", 0) for r in rows) / len(rows)

    report.summaries["avg_daily_steps"] = f"{avg_steps:,.0f}"
    report.summaries["avg_active_minutes"] = f"{avg_active:.0f} min"

    streak = _trailing_streak([s < STEPS_SEDENTARY for s in steps_list])
    if streak >= STEPS_SEDENTARY_STREAK:
        report.alerts.append(
            TrendAlert(
                category="activity",
                severity="warning",
                key="sedentary_streak",
                message=(
                    f"Fewer than {STEPS_SEDENTARY:,} steps for {streak} consecutive days "
                    f"(avg {avg_steps:,.0f} steps). Even a 15-minute walk helps."
                ),
                data={"streak_days": streak, "avg_steps": round(avg_steps)},
            )
        )
    elif avg_steps < STEPS_GOAL:
        report.alerts.append(
            TrendAlert(
                category="activity",
                severity="info",
                key="below_step_goal",
                message=(
                    f"Averaging {avg_steps:,.0f} steps/day vs goal of {STEPS_GOAL:,}. "
                    "Short walking breaks during calls add up quickly."
                ),
                data={"avg_steps": round(avg_steps)},
            )
        )

    if avg_active < ACTIVE_MINUTES_GOAL:
        report.alerts.append(
            TrendAlert(
                category="activity",
                severity="info",
                key="insufficient_active_minutes",
                message=(
                    f"Averaging {avg_active:.0f} active minutes/day, "
                    f"below the WHO-recommended {ACTIVE_MINUTES_GOAL} minutes."
                ),
                data={"avg_active_minutes": round(avg_active)},
            )
        )


# ── Heart rate ────────────────────────────────────────────────────────────────


def _analyse_heart_rate(rows: list[Any], report: TrendReport) -> None:
    rhr_values = [
        r.data.get("resting_heart_rate")
        for r in rows
        if r.data.get("resting_heart_rate") is not None
    ]
    if not rhr_values:
        return

    avg_rhr = sum(rhr_values) / len(rhr_values)
    report.summaries["avg_resting_hr"] = f"{avg_rhr:.0f} bpm"

    if avg_rhr >= RHR_CRITICAL:
        report.alerts.append(
            TrendAlert(
                category="heart_rate",
                severity="critical",
                key="elevated_resting_hr",
                message=(
                    f"Average resting heart rate is {avg_rhr:.0f} bpm — above normal range. "
                    "Please consider consulting a healthcare professional."
                ),
                data={"avg_rhr": round(avg_rhr)},
            )
        )
    elif avg_rhr >= RHR_ELEVATED:
        report.alerts.append(
            TrendAlert(
                category="heart_rate",
                severity="warning",
                key="slightly_elevated_rhr",
                message=(
                    f"Resting heart rate averaged {avg_rhr:.0f} bpm this week. "
                    "Stress, poor sleep, and dehydration can elevate resting HR."
                ),
                data={"avg_rhr": round(avg_rhr)},
            )
        )

    avg_cardio = sum(
        r.data.get("zones", {}).get("cardio_minutes", 0)
        + r.data.get("zones", {}).get("peak_minutes", 0)
        for r in rows
    ) / len(rows)

    if avg_cardio > CARDIO_PEAK_OVERTRAINING:
        report.alerts.append(
            TrendAlert(
                category="heart_rate",
                severity="info",
                key="overtraining_risk",
                message=(
                    f"Averaging {avg_cardio:.0f} min/day in cardio/peak zones. "
                    "Ensure adequate rest days to prevent overtraining."
                ),
                data={"avg_cardio_peak_minutes": round(avg_cardio)},
            )
        )


# ── Utility ───────────────────────────────────────────────────────────────────


def _trailing_streak(flags: list[bool]) -> int:
    count = 0
    for val in reversed(flags):
        if val:
            count += 1
        else:
            break
    return count
