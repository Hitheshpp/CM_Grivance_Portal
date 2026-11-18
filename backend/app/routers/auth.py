from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..constants import ROLE_CITIZEN
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, RegisterIn
from ..security import RateLimiter, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth"])

login_limit = RateLimiter(10, 60, "login")
register_limit = RateLimiter(5, 60, "registration")


def user_out(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email, "mobile": u.mobile, "role": u.role,
            "department_id": u.department_id, "department": u.department.name if u.department else None}


@router.post("/register", status_code=201, dependencies=[Depends(register_limit)])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    """Public self-registration. Always creates a *citizen*; CMO/officer accounts are provisioned by admins."""
    email = body.email.lower()
    if db.scalar(select(User).where(func.lower(User.email) == email)):
        raise HTTPException(409, "An account with this email already exists")
    user = User(name=body.name, email=email, mobile=body.mobile, password_hash=hash_password(body.password),
                role=ROLE_CITIZEN)
    db.add(user)
    db.commit()
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer", "user": user_out(user)}


@router.post("/login", dependencies=[Depends(login_limit)])
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.strip().lower()))
    # Same message for unknown email and wrong password (no account enumeration).
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer", "user": user_out(user)}


@router.post("/logout")
def logout(_: User = Depends(get_current_user)):
    """JWTs are stateless: logout is completed client-side by discarding the token (8h expiry)."""
    return {"message": "Logged out. Please discard the token on the client."}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_out(user)
