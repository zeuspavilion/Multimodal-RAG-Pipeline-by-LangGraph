import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from backend.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES


# ---------------------------------
# Password hashing
# ---------------------------------

def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


# ---------------------------------
# JWT issuing + verification
# ---------------------------------

def create_access_token(user_id: str, email: str) -> str:
    """Issue a signed JWT containing user_id and email."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,          # standard JWT claim — subject of the token
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure —
    caller (FastAPI dependency) is responsible for converting these to HTTP 401.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])