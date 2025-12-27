from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from jose import JWTError, jwt
import httpx

from app.database import get_db
from app.models import User
from app.schemas import schemas
from app.core import security
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=schemas.User)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="User with this username or email already exists"
        )
    
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        reputation_score=0.0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=schemas.Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/google", response_model=schemas.Token)
async def google_login(request: schemas.SocialLoginRequest, db: Session = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": request.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": "postmessage", # Common for SPAs
            },
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to exchange Google code: {response.text}")
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # Get user info
        user_info_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if user_info_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Google user info")
        
        user_info = user_info_res.json()
        email = user_info.get("email")
        google_id = user_info.get("sub")
        avatar = user_info.get("picture")
        name = user_info.get("name") or email.split("@")[0]

    # Find or create user
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
            if not user.avatar:
                user.avatar = avatar
        else:
            # Ensure unique username
            base_username = name.replace(" ", "").lower()
            username = base_username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User(
                email=email,
                username=username,
                google_id=google_id,
                avatar=avatar,
                reputation_score=0.0
            )
            db.add(user)
        db.commit()
        db.refresh(user)

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": jwt_token, "token_type": "bearer"}


@router.post("/github", response_model=schemas.Token)
async def github_login(request: schemas.SocialLoginRequest, db: Session = Depends(get_db)):
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")

    async with httpx.AsyncClient() as client:
        # Exchange code for token
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": request.code,
            },
            headers={"Accept": "application/json"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to exchange GitHub code: {response.text}")
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail=f"No access token returned from GitHub: {token_data}")
        
        # Get user info
        user_info_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"}
        )
        if user_info_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get GitHub user info")
        
        user_info = user_info_res.json()
        github_id = str(user_info.get("id"))
        username_github = user_info.get("login")
        avatar = user_info.get("avatar_url")
        email = user_info.get("email")
        
        if not email:
            # GitHub might not return email if it's private, need to fetch it separately
            emails_res = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {access_token}"}
            )
            if emails_res.status_code == 200:
                emails = emails_res.json()
                primary_email = next((e["email"] for e in emails if e["primary"]), None)
                email = primary_email or emails[0]["email"]
            else:
                raise HTTPException(status_code=400, detail="Failed to get GitHub user email")

    # Find or create user
    user = db.query(User).filter(User.github_id == github_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.github_id = github_id
            if not user.avatar:
                user.avatar = avatar
        else:
            # Ensure unique username
            base_username = username_github.lower()
            username = base_username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User(
                email=email,
                username=username,
                github_id=github_id,
                avatar=avatar,
                reputation_score=0.0
            )
            db.add(user)
        db.commit()
        db.refresh(user)

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": jwt_token, "token_type": "bearer"}
