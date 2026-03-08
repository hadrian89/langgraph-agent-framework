from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException

SECRET_KEY = "CHANGE_THIS_SECRET"
ALGORITHM = "HS256"


def create_token(user_id: str):

    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token


def verify_token(token: str):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")