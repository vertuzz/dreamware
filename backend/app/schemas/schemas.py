from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl
from app.models import VibeStatus, NotificationType

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    avatar: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    reputation_score: Optional[float] = None

class UserLinkBase(BaseModel):
    label: str
    url: str

class UserLink(UserLinkBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    id: int
    reputation_score: float
    links: List[UserLink] = []
    model_config = ConfigDict(from_attributes=True)

# Tool & Tag Schemas
class ToolBase(BaseModel):
    name: str

class Tool(ToolBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TagBase(BaseModel):
    name: str

class Tag(TagBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Vibe Image
class VibeImageBase(BaseModel):
    image_url: str

class VibeImage(VibeImageBase):
    id: int
    vibe_id: int
    model_config = ConfigDict(from_attributes=True)

# Vibe
class VibeBase(BaseModel):
    prompt_text: str
    prd_text: Optional[str] = None
    extra_specs: Optional[dict] = None
    status: VibeStatus = VibeStatus.CONCEPT

class VibeCreate(VibeBase):
    parent_vibe_id: Optional[int] = None
    tool_ids: List[int] = []
    tag_ids: List[int] = []

class VibeUpdate(BaseModel):
    prompt_text: Optional[str] = None
    prd_text: Optional[str] = None
    extra_specs: Optional[dict] = None
    status: Optional[VibeStatus] = None

class Vibe(VibeBase):
    id: int
    creator_id: int
    parent_vibe_id: Optional[int] = None
    created_at: datetime
    images: List[VibeImage] = []
    tools: List[Tool] = []
    tags: List[Tag] = []
    model_config = ConfigDict(from_attributes=True)

# Implementation
class ImplementationBase(BaseModel):
    url: str
    description: Optional[str] = None
    is_official: bool = False

class ImplementationCreate(ImplementationBase):
    pass

class Implementation(ImplementationBase):
    id: int
    vibe_id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Comment
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    vibe_id: int
    user_id: int
    created_at: datetime
    likes_count: int
    model_config = ConfigDict(from_attributes=True)

# Review
class ReviewBase(BaseModel):
    score: float
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: int
    vibe_id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Like
class Like(BaseModel):
    id: int
    vibe_id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Collection
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True

class CollectionCreate(CollectionBase):
    vibe_ids: List[int] = []

class Collection(CollectionBase):
    id: int
    owner_id: int
    created_at: datetime
    vibes: List[Vibe] = []
    model_config = ConfigDict(from_attributes=True)

# Notification
class Notification(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    content: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SocialLoginRequest(BaseModel):
    code: str

# Media
class MediaResponse(BaseModel):
    upload_url: str
    download_url: str
    file_key: str

class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str
