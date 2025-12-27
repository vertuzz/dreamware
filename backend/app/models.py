import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import JSON, ForeignKey, Float, Table, Text, DateTime, func, String, Column, Enum, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

# Association tables
vibe_tools = Table(
    "vibe_tools",
    Base.metadata,
    Column("vibe_id", ForeignKey("vibes.id"), primary_key=True),
    Column("tool_id", ForeignKey("tools.id"), primary_key=True),
)

vibe_tags = Table(
    "vibe_tags",
    Base.metadata,
    Column("vibe_id", ForeignKey("vibes.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

collection_vibes = Table(
    "collection_vibes",
    Base.metadata,
    Column("collection_id", ForeignKey("collections.id"), primary_key=True),
    Column("vibe_id", ForeignKey("vibes.id"), primary_key=True),
)

class VibeStatus(str, enum.Enum):
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

    vibes: Mapped[List["Vibe"]] = relationship("Vibe", back_populates="creator")
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

    vibes: Mapped[List["Vibe"]] = relationship("Vibe", secondary=vibe_tools, back_populates="tools")

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    vibes: Mapped[List["Vibe"]] = relationship("Vibe", secondary=vibe_tags, back_populates="tags")

class VibeImage(Base):
    __tablename__ = "vibe_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vibe_id: Mapped[int] = mapped_column(ForeignKey("vibes.id"), index=True)
    image_url: Mapped[str] = mapped_column(String(512))
    
    vibe: Mapped["Vibe"] = relationship("Vibe", back_populates="images")

class Vibe(Base):
    __tablename__ = "vibes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Core content
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    prd_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_specs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Lineage
    parent_vibe_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vibes.id"), nullable=True, index=True)
    
    status: Mapped[VibeStatus] = mapped_column(Enum(VibeStatus), default=VibeStatus.CONCEPT, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="vibes")
    images: Mapped[List["VibeImage"]] = relationship("VibeImage", back_populates="vibe", cascade="all, delete-orphan")
    tools: Mapped[List["Tool"]] = relationship("Tool", secondary=vibe_tools, back_populates="vibes")
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=vibe_tags, back_populates="vibes")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="vibe", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="vibe", cascade="all, delete-orphan")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="vibe", cascade="all, delete-orphan")
    implementations: Mapped[List["Implementation"]] = relationship("Implementation", back_populates="vibe", cascade="all, delete-orphan")
    
    parent: Mapped[Optional["Vibe"]] = relationship("Vibe", remote_side=[id], back_populates="forks")
    forks: Mapped[List["Vibe"]] = relationship("Vibe", back_populates="parent")

class Implementation(Base):
    __tablename__ = "implementations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vibe_id: Mapped[int] = mapped_column(ForeignKey("vibes.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    vibe: Mapped["Vibe"] = relationship("Vibe", back_populates="implementations")
    user: Mapped["User"] = relationship("User", back_populates="implementations")

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vibe_id: Mapped[int] = mapped_column(ForeignKey("vibes.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Counter cache for performance
    likes_count: Mapped[int] = mapped_column(default=0)

    vibe: Mapped["Vibe"] = relationship("Vibe", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")
    likes: Mapped[List["CommentLike"]] = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vibe_id: Mapped[int] = mapped_column(ForeignKey("vibes.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    vibe: Mapped["Vibe"] = relationship("Vibe", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")

class Like(Base):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vibe_id: Mapped[int] = mapped_column(ForeignKey("vibes.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    vibe: Mapped["Vibe"] = relationship("Vibe", back_populates="likes")
    user: Mapped["User"] = relationship("User", back_populates="likes")

    # Ensure a user can only like a vibe once
    __table_args__ = (UniqueConstraint("vibe_id", "user_id", name="uq_vibe_like"),)

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
    vibes: Mapped[List["Vibe"]] = relationship("Vibe", secondary=collection_vibes)

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
