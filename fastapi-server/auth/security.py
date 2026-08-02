import os
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_EXPIRE_MINUTES", "30")
)
REFRESH_EXPIRE_DAYS = int(
    os.getenv("REFRESH_EXPIRE_DAYS", "7")
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str):
    return pwd_context.hash(password[:72].encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))

def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )

def create_access_token(user_id: str):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow()
        + timedelta(minutes=ACCESS_EXPIRE_MINUTES)
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def create_refresh_token(user_id: str):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow()
        + timedelta(days=REFRESH_EXPIRE_DAYS)
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )