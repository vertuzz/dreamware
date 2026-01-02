from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl
from app.models import DreamStatus, NotificationType

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
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

class UserLinkBase(BaseModel):
    label: str
    url: str

class UserLink(UserLinkBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)

class UserPublic(BaseModel):
    id: int
    username: str
    avatar: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    reputation_score: float
    is_admin: bool = False
    links: List[UserLink] = []
    model_config = ConfigDict(from_attributes=True)

class User(UserPublic):
    email: EmailStr
    api_key: Optional[str] = None

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

# Dream Creator (for embedding in Dream)
class DreamCreator(BaseModel):
    id: int
    username: str
    avatar: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Dream Media
class DreamMediaBase(BaseModel):
    media_url: str

class DreamMedia(DreamMediaBase):
    id: int
    dream_id: int
    model_config = ConfigDict(from_attributes=True)

# Dream
class DreamBase(BaseModel):
    title: Optional[str] = None
    prompt_text: Optional[str] = None
    prd_text: Optional[str] = None
    extra_specs: Optional[dict] = None
    status: DreamStatus = DreamStatus.CONCEPT
    app_url: Optional[str] = None
    youtube_url: Optional[str] = None
    is_agent_submitted: bool = False
    is_owner: bool = False

class DreamCreate(DreamBase):
    parent_dream_id: Optional[int] = None
    tool_ids: List[int] = []
    tag_ids: List[int] = []

class DreamUpdate(BaseModel):
    title: Optional[str] = None
    prompt_text: Optional[str] = None
    prd_text: Optional[str] = None
    extra_specs: Optional[dict] = None
    status: Optional[DreamStatus] = None
    app_url: Optional[str] = None
    youtube_url: Optional[str] = None
    is_agent_submitted: Optional[bool] = None
    is_owner: Optional[bool] = None
    tool_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None

class Dream(DreamBase):
    id: int
    slug: str
    creator_id: int
    parent_dream_id: Optional[int] = None
    created_at: datetime
    media: List[DreamMedia] = []
    tools: List[Tool] = []
    tags: List[Tag] = []
    creator: Optional[DreamCreator] = None
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    is_owner: bool
    model_config = ConfigDict(from_attributes=True)

# Implementation
class ImplementationBase(BaseModel):
    url: str
    description: Optional[str] = None

class ImplementationCreate(ImplementationBase):
    pass

class Implementation(ImplementationBase):
    id: int
    dream_id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Comment
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    parent_id: Optional[int] = None

class Comment(CommentBase):
    id: int
    dream_id: int
    user_id: int
    created_at: datetime
    created_at: datetime
    score: int
    parent_id: Optional[int] = None
    user_vote: int = 0  # 0: none, 1: up, -1: down
    model_config = ConfigDict(from_attributes=True)

class CommentUser(BaseModel):
    id: int
    username: str
    avatar: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class CommentWithUser(Comment):
    user: Optional[CommentUser] = None
    model_config = ConfigDict(from_attributes=True)

# Review
class ReviewBase(BaseModel):
    score: float
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: int
    dream_id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Like
class Like(BaseModel):
    id: int
    dream_id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Collection
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True

class CollectionCreate(CollectionBase):
    dream_ids: List[int] = []

class Collection(CollectionBase):
    id: int
    owner_id: int
    created_at: datetime
    dreams: List[Dream] = []
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

class DreamPublic(BaseModel):
    id: int
    title: Optional[str] = None
    slug: str
    model_config = ConfigDict(from_attributes=True)

# Ownership Claim Schemas
from app.models import ClaimStatus

class OwnershipClaimCreate(BaseModel):
    message: Optional[str] = None

class OwnershipClaim(BaseModel):
    id: int
    dream_id: int
    claimant_id: int
    message: Optional[str] = None
    status: ClaimStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class OwnershipClaimWithDetails(OwnershipClaim):
    claimant: Optional[DreamCreator] = None
    dream: Optional[DreamPublic] = None
