from fastapi import Header, HTTPException
import jwt

from backend.utils.auth import decode_access_token
from backend.db.users import get_user_by_id


async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Extracts and verifies the JWT from the Authorization header.
    Expected header format: "Bearer <token>"
    Returns the user dict {id, email, name} on success.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format.")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    return user