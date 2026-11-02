"""
auth.py - Authentication and Authorization in one simple file.

AUTHENTICATION = "Who are you?"
    The user sends username + password to /auth/login.
    If they are correct, we give back a TOKEN (a JWT).
    After that, the user sends this token with every request
    in the header:   Authorization: Bearer <token>

AUTHORIZATION = "What are you allowed to do?"
    Every user has a ROLE: "user" or "admin".
    Some endpoints only allow admins. Some only let you touch your own data.

Flow:
    1. POST /auth/register  -> create an account (password is stored HASHED)
    2. POST /auth/login     -> get a token
    3. Call protected endpoints with the token
"""

import json
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# 1. SETTINGS
# ---------------------------------------------------------------------------

# The secret key is used to SIGN tokens. Anyone who knows it can make fake
# tokens, so in real projects keep it in an environment variable.
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

USERS_FILE = "users.json"  # users are saved here (like data.json for documents)

# This tells FastAPI: "the token comes from the Authorization header, and
# users get it from /auth/login". It also adds the "Authorize" button in /docs.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------------------------------------------------------------------
# 2. MODELS
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    """What we send back about a user. Notice: NO password here."""
    username: str
    role: str


# ---------------------------------------------------------------------------
# 3. SAVING / LOADING USERS (JSON file)
# ---------------------------------------------------------------------------

def read_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)


def find_user(username: str):
    for user in read_users():
        if user["username"] == username:
            return user
    return None


# ---------------------------------------------------------------------------
# 4. PASSWORD HASHING
#    We NEVER store the real password. We store a "hash" (scrambled version).
#    To check a password, we hash what the user typed and compare.
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# 5. TOKENS (JWT)
#    A JWT is a small signed string that says "this is user X, role Y,
#    valid until time Z". The server can trust it because only the server
#    knows SECRET_KEY.
# ---------------------------------------------------------------------------

def create_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    data = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 6. DEPENDENCIES - these are what you add to your endpoints
# ---------------------------------------------------------------------------

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    AUTHENTICATION check.
    Add `user = Depends(get_current_user)` to any endpoint to make it
    "logged-in users only". It reads the token, checks it, and returns the user.
    """
    login_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except jwt.PyJWTError:  # wrong signature, expired, broken token...
        raise login_error

    user = find_user(username)
    if user is None:
        raise login_error

    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    AUTHORIZATION check.
    Add `user = Depends(require_admin)` to make an endpoint "admins only".
    It first runs get_current_user (must be logged in), then checks the role.
    """
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can do this",
        )
    return user


# ---------------------------------------------------------------------------
# 7. AUTH ENDPOINTS
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserOut)
def register(new_user: UserRegister):
    users = read_users()

    if find_user(new_user.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    # Simple rule: the FIRST person to register becomes admin.
    role = "admin" if len(users) == 0 else "user"

    users.append({
        "username": new_user.username,
        "password": hash_password(new_user.password),  # stored hashed!
        "role": role,
    })
    save_users(users)

    return {"username": new_user.username, "role": role}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    Send username + password as form data. Returns a token.
    (Form data is the standard for OAuth2, and it makes the
    "Authorize" button in /docs work.)
    """
    user = find_user(form.username)

    if user is None or not verify_password(form.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong username or password",
        )

    token = create_token(user["username"], user["role"])
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def read_me(user: dict = Depends(get_current_user)):
    """Returns the logged-in user. Good for testing your token."""
    return user
