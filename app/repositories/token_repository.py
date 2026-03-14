from sqlalchemy import text

from app.db import SessionLocal


def save_fitbit_tokens(user_id, access_token, refresh_token):

    db = SessionLocal()

    db.execute(
        text(
            """
        INSERT INTO wearable_tokens
        (user_id, provider, access_token, refresh_token)
        VALUES (:user_id, 'fitbit', :access_token, :refresh_token)
        """
        ),
        {
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    )

    db.commit()
    db.close()
