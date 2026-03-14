from sqlalchemy import text

from app.db import SessionLocal


def get_recent_health_metrics(user_id, days=7):

    db = SessionLocal()

    result = db.execute(
        text(
            """
            SELECT date, steps, sleep_hours
            FROM health_metrics
            WHERE user_id = :user_id
            ORDER BY date DESC
            LIMIT :days
            """
        ),
        {"user_id": user_id, "days": days},
    )

    rows = result.fetchall()

    db.close()

    return rows
