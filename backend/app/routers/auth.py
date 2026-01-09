from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import timedelta
from typing import Optional
from jose import JWTError, jwt
import httpx

from app.database import get_db
from app.models import User
from app.schemas import schemas
from app.core import security
from app.core.security import SECRET_KEY, ALGORITHM, generate_api_key
from app.core.config import settings
from app.services.telegram import notify_new_user

router = APIRouter()

# OAuth2 scheme - tokenUrl is kept for OpenAPI docs compatibility
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(
    db: AsyncSession = Depends(get_db), 
    token: str = Depends(oauth2_scheme_optional),
    api_key: Optional[str] = Depends(api_key_header)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = None
    
    # Try API Key first
    if api_key:
        result = await db.execute(
            select(User).options(selectinload(User.links)).filter(User.api_key == api_key)
        )
        user = result.scalars().first()
    
    # Try JWT if API Key didn't work or wasn't provided
    if not user and token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id_str: str = payload.get("sub")
            if user_id_str:
                user_id = int(user_id_str)
                result = await db.execute(
                    select(User).options(selectinload(User.links)).filter(User.id == user_id)
                )
                user = result.scalars().first()
        except (JWTError, ValueError):
            pass

    if user is None:
        raise credentials_exception
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that ensures the current user is an admin.
    Use this for admin-only endpoints.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_current_user_optional(
    db: AsyncSession = Depends(get_db), 
    token: Optional[str] = Depends(oauth2_scheme_optional),
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[User]:
    user = None
    
    # Try API Key first
    if api_key:
        result = await db.execute(
            select(User).options(selectinload(User.links)).filter(User.api_key == api_key)
        )
        user = result.scalars().first()
        if user:
            return user
            
    # Try JWT
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id_str: str = payload.get("sub")
            if user_id_str:
                user_id = int(user_id_str)
                result = await db.execute(
                    select(User).options(selectinload(User.links)).filter(User.id == user_id)
                )
                user = result.scalars().first()
        except (JWTError, ValueError):
            return None
    
    return user

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/google", response_model=schemas.Token)
async def google_login(request: schemas.SocialLoginRequest, db: AsyncSession = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    # Exchange code for token
    # Use provided redirect_uri or fall back to "postmessage" for legacy support
    redirect_uri = request.redirect_uri or "postmessage"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": request.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
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
    result = await db.execute(
        select(User).options(selectinload(User.links)).filter(User.google_id == google_id)
    )
    user = result.scalars().first()
    is_new_user = False
    if not user:
        result = await db.execute(
            select(User).options(selectinload(User.links)).filter(User.email == email)
        )
        user = result.scalars().first()
        if user:
            user.google_id = google_id
            if not user.avatar:
                user.avatar = avatar
        else:
            # Ensure unique username
            base_username = name.replace(" ", "").lower()
            username = base_username
            counter = 1
            while True:
                result = await db.execute(select(User).filter(User.username == username))
                if not result.scalars().first():
                    break
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User(
                email=email,
                username=username,
                google_id=google_id,
                api_key=generate_api_key(),
                avatar=avatar,
                reputation_score=0.0
            )
            db.add(user)
            is_new_user = True
        await db.commit()
        if is_new_user:
            notify_new_user(username, "Google")
        # Reload with eager loading
        result = await db.execute(
            select(User).options(selectinload(User.links)).filter(User.id == user.id)
        )
        user = result.scalars().first()

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": jwt_token, "token_type": "bearer"}


@router.post("/github", response_model=schemas.Token)
async def github_login(request: schemas.SocialLoginRequest, db: AsyncSession = Depends(get_db)):
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
    result = await db.execute(
        select(User).options(selectinload(User.links)).filter(User.github_id == github_id)
    )
    user = result.scalars().first()
    is_new_user = False
    if not user:
        result = await db.execute(
            select(User).options(selectinload(User.links)).filter(User.email == email)
        )
        user = result.scalars().first()
        if user:
            user.github_id = github_id
            if not user.avatar:
                user.avatar = avatar
        else:
            # Ensure unique username
            base_username = username_github.lower()
            username = base_username
            counter = 1
            while True:
                result = await db.execute(select(User).filter(User.username == username))
                if not result.scalars().first():
                    break
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User(
                email=email,
                username=username,
                github_id=github_id,
                api_key=generate_api_key(),
                avatar=avatar,
                reputation_score=0.0
            )
            db.add(user)
            is_new_user = True
        await db.commit()
        if is_new_user:
            notify_new_user(username, "GitHub")
        # Reload with eager loading
        result = await db.execute(
            select(User).options(selectinload(User.links)).filter(User.id == user.id)
        )
        user = result.scalars().first()

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": jwt_token, "token_type": "bearer"}


@router.post("/api-key/regenerate", response_model=schemas.User)
async def regenerate_api_key(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate the API key for the current user.
    """
    current_user.api_key = generate_api_key()
    db.add(current_user)
    await db.commit()
    
    # Reload with eager loading
    result = await db.execute(
        select(User).options(selectinload(User.links)).filter(User.id == current_user.id)
    )
    return result.scalars().first()
