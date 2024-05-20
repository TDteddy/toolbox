from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
import logging

from auth import authenticate_user, fake_users_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
AUTHORIZATION_CODES = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_clients_db = {
    "your_client_id": {
        "client_secret": "your_client_secret",
        "redirect_uris": ["https://chat.openai.com/aip/g-49a70c6e3c718b9d5e342b6bea6497755b2c071b/oauth/callback"]
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_client(client_id: str, client_secret: str) -> bool:
    logger.info(f"Authenticating client_id: {client_id}")
    client = fake_clients_db.get(client_id)
    if not client:
        logger.error("Client not found")
        return False
    if client["client_secret"] != client_secret:
        logger.error("Invalid client secret")
        return False
    logger.info("Client authenticated successfully")
    return True


router = APIRouter()

@router.get("/authorize")
async def authorize(client_id: str, redirect_uri: str, response_type: str, state: str, request: Request):
    client = fake_clients_db.get(client_id)
    if not client or redirect_uri not in client["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid client or redirect URI")
    return RedirectResponse(
        url=f"/static/login.html?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&state={state}")

@router.post("/login")
async def login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        client_id: str = Form(...),
        redirect_uri: str = Form(...),
        response_type: str = Form(...),
        state: str = Form(...)
):
    logger.info(f"Login attempt with username: {username}")
    user = authenticate_user(fake_users_db, username, password)
    if not user:
        logger.error(f"Login failed for username: {username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if response_type != "code":
        logger.error(f"Unsupported response type: {response_type}")
        raise HTTPException(status_code=400, detail="Unsupported response type")

    code = str(uuid4())
    AUTHORIZATION_CODES[code] = {
        "username": user["username"],
        "redirect_uri": redirect_uri
    }

    redirect_url = f"{redirect_uri}?code={code}&state={state}"
    logger.info(f"Redirecting to: {redirect_url}")
    return RedirectResponse(url=redirect_url, status_code=302)

@router.post("/token")
async def oauth2_token(
        grant_type: str = Form(...),
        client_id: str = Form(...),
        client_secret: str = Form(...),
        code: str = Form(None),
        redirect_uri: str = Form(None),
        username: str = Form(None),
        password: str = Form(None),
        refresh_token: str = Form(None),
):
    if grant_type == "authorization_code":
        if not (await authenticate_client(client_id, client_secret)):
            raise HTTPException(status_code=400, detail="Invalid client credentials")
        if code not in AUTHORIZATION_CODES:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        user_info = AUTHORIZATION_CODES.pop(code)
        if redirect_uri != user_info["redirect_uri"]:
            raise HTTPException(status_code=400, detail="Invalid redirect URI")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_info["username"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Unsupported grant type")

