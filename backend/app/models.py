import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import JSON, ForeignKey, Float, Table, Text, DateTime, func, String, Column, Enum, Boolean, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

# Association tables
dream_tools = Table(
    "dream_tools",
    Base.metadata,
    Column("dream_id", ForeignKey("dreams.id"), primary_key=True),
    Column("tool_id", ForeignKey("tools.id"), primary_key=True),
)

dream_tags = Table(
    "dream_tags",
    Base.metadata,
    Column("dream_id", ForeignKey("dreams.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

collection_dreams = Table(
    "collection_dreams",
    Base.metadata,
    Column("collection_id", ForeignKey("collections.id"), primary_key=True),
    Column("dream_id", ForeignKey("dreams.id"), primary_key=True),
)

class DreamStatus(str, enum.Enum):
    CONCEPT = "Concept"
    WIP = "WIP"
    LIVE = "Live"

class NotificationType(str, enum.Enum):
    LIKE = "like"
    COMMENT = "comment"
    FORK = "fork"
    IMPLEMENTATION = "implementation"

class Follow(Base):
    __tablename__ = "follows"
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    followed_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reputation_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    
    # Auth fields
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    github_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)

    dreams: Mapped[List["Dream"]] = relationship("Dream", back_populates="creator")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    comment_likes: Mapped[List["CommentLike"]] = relationship("CommentLike", back_populates="user", cascade="all, delete-orphan")
    collections: Mapped[List["Collection"]] = relationship("Collection", back_populates="owner", cascade="all, delete-orphan")
    implementations: Mapped[List["Implementation"]] = relationship("Implementation", back_populates="user", cascade="all, delete-orphan")
    links: Mapped[List["UserLink"]] = relationship("UserLink", back_populates="user", cascade="all, delete-orphan")
    
    # Self-referential for followers
    followers: Mapped[List["User"]] = relationship(
        "User",
        secondary="follows",
        primaryjoin=id == Follow.followed_id,
        secondaryjoin=id == Follow.follower_id,
        back_populates="following"
    )
    following: Mapped[List["User"]] = relationship(
        "User",
        secondary="follows",
        primaryjoin=id == Follow.follower_id,
        secondaryjoin=id == Follow.followed_id,
        back_populates="followers"
    )

    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class UserLink(Base):
    __tablename__ = "user_links"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(50)) # e.g., 'GitHub', 'Twitter', 'Portfolio'
    url: Mapped[str] = mapped_column(String(512))

    user: Mapped["User"] = relationship("User", back_populates="links")

class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    dreams: Mapped[List["Dream"]] = relationship("Dream", secondary=dream_tools, back_populates="tools")

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    dreams: Mapped[List["Dream"]] = relationship("Dream", secondary=dream_tags, back_populates="tags")

class DreamMedia(Base):
    __tablename__ = "dream_media"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dream_id: Mapped[int] = mapped_column(ForeignKey("dreams.id"), index=True)
    media_url: Mapped[str] = mapped_column(String(512))
    
    dream: Mapped["Dream"] = relationship("Dream", back_populates="media")

class Dream(Base):
    __tablename__ = "dreams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Core content
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prompt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prd_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_specs: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)
    
    # New fields for Dreamware v2.0
    app_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    youtube_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_agent_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Lineage
    parent_dream_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dreams.id"), nullable=True, index=True)
    
    status: Mapped[DreamStatus] = mapped_column(Enum(DreamStatus), default=DreamStatus.CONCEPT, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="dreams")
    media: Mapped[List["DreamMedia"]] = relationship("DreamMedia", back_populates="dream", cascade="all, delete-orphan")
    tools: Mapped[List["Tool"]] = relationship("Tool", secondary=dream_tools, back_populates="dreams")
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=dream_tags, back_populates="dreams")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="dream", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="dream", cascade="all, delete-orphan")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="dream", cascade="all, delete-orphan")
    implementations: Mapped[List["Implementation"]] = relationship("Implementation", back_populates="dream", cascade="all, delete-orphan")
    
    parent: Mapped[Optional["Dream"]] = relationship("Dream", remote_side=[id], back_populates="forks")
    forks: Mapped[List["Dream"]] = relationship("Dream", back_populates="parent")

class Implementation(Base):
    __tablename__ = "implementations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dream_id: Mapped[int] = mapped_column(ForeignKey("dreams.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    dream: Mapped["Dream"] = relationship("Dream", back_populates="implementations")
    user: Mapped["User"] = relationship("User", back_populates="implementations")

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dream_id: Mapped[int] = mapped_column(ForeignKey("dreams.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Counter cache for performance
    likes_count: Mapped[int] = mapped_column(default=0)

    dream: Mapped["Dream"] = relationship("Dream", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")
    likes: Mapped[List["CommentLike"]] = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dream_id: Mapped[int] = mapped_column(ForeignKey("dreams.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    dream: Mapped["Dream"] = relationship("Dream", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")

class Like(Base):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dream_id: Mapped[int] = mapped_column(ForeignKey("dreams.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    dream: Mapped["Dream"] = relationship("Dream", back_populates="likes")
    user: Mapped["User"] = relationship("User", back_populates="likes")

    # Ensure a user can only like a dream once
    __table_args__ = (UniqueConstraint("dream_id", "user_id", name="uq_dream_like"),)

class CommentLike(Base):
    __tablename__ = "comment_likes"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    comment: Mapped["Comment"] = relationship("Comment", back_populates="likes")
    user: Mapped["User"] = relationship("User", back_populates="comment_likes")

    # Ensure a user can only like a comment once
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_like"),)

class Collection(Base):
    __tablename__ = "collections"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    is_public: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    owner: Mapped["User"] = relationship("User", back_populates="collections")
    dreams: Mapped[List["Dream"]] = relationship("Dream", secondary=collection_dreams)

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    content: Mapped[str] = mapped_column(Text)
    link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped["User"] = relationship("User", back_populates="notifications")
