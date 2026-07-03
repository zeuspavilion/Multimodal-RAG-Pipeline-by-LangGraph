from fastapi import APIRouter, HTTPException, Depends

from backend.api.schemas import SignupRequest, LoginRequest, AuthResponse, UserResponse
from backend.db.users import get_user_by_email, create_user
from backend.utils.auth import hash_password, verify_password, create_access_token
from backend.api.dependencies import get_current_user

router = APIRouter()


@router.post("/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    existing = await get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    password_hash = hash_password(request.password)
    user = await create_user(
        email=request.email,
        password_hash=password_hash,
        name=request.name
    )

    token = create_access_token(user_id=str(user["id"]), email=user["email"])

    return AuthResponse(
        access_token=token,
        user=UserResponse(id=str(user["id"]), name=user["name"], email=user["email"])
    )


@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    user = await get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="No account found with this email. Please sign up first."
        )
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")


    token = create_access_token(user_id=str(user["id"]), email=user["email"])

    return AuthResponse(
        access_token=token,
        user=UserResponse(id=str(user["id"]), name=user["name"], email=user["email"])
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["id"]),
        name=current_user["name"],
        email=current_user["email"]
    )