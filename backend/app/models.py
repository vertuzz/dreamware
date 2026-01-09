import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import JSON, ForeignKey, Float, Table, Text, DateTime, func, String, Column, Enum, Boolean, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

# Association tables
app_tools = Table(
    "app_tools",
    Base.metadata,
    Column("app_id", ForeignKey("apps.id"), primary_key=True),
    Column("tool_id", ForeignKey("tools.id"), primary_key=True),
)

app_tags = Table(
    "app_tags",
    Base.metadata,
    Column("app_id", ForeignKey("apps.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

collection_apps = Table(
    "collection_apps",
    Base.metadata,
    Column("collection_id", ForeignKey("collections.id"), primary_key=True),
    Column("app_id", ForeignKey("apps.id"), primary_key=True),
)

class AppStatus(str, enum.Enum):
    CONCEPT = "Concept"
    WIP = "WIP"
    LIVE = "Live"

class NotificationType(str, enum.Enum):
    LIKE = "LIKE"
    COMMENT = "COMMENT"
    FORK = "FORK"
    IMPLEMENTATION = "IMPLEMENTATION"
    FOLLOW = "FOLLOW"
    OWNERSHIP_CLAIM = "OWNERSHIP_CLAIM"

class FeedbackType(str, enum.Enum):
    BUG = "bug"
    FEATURE = "feature"
    OTHER = "other"

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
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reputation_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Auth fields (OAuth only - no password)
    google_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    github_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)

    apps: Mapped[List["App"]] = relationship("App", back_populates="creator")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    comment_votes: Mapped[List["CommentVote"]] = relationship("CommentVote", back_populates="user", cascade="all, delete-orphan")
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

    apps: Mapped[List["App"]] = relationship("App", secondary=app_tools, back_populates="tools")

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    apps: Mapped[List["App"]] = relationship("App", secondary=app_tags, back_populates="tags")

class AppMedia(Base):
    __tablename__ = "app_media"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), index=True)
    media_url: Mapped[str] = mapped_column(String(512))
    
    app: Mapped["App"] = relationship("App", back_populates="media")

class App(Base):
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Core content
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prompt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prd_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_specs: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)
    
    # New fields for v2.0
    app_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    youtube_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_agent_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Lineage
    parent_app_id: Mapped[Optional[int]] = mapped_column(ForeignKey("apps.id"), nullable=True, index=True)
    
    # Dead app tracking
    is_dead: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Source tracking for ingested posts (e.g., Reddit permalink)
    post_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True)
    
    status: Mapped[AppStatus] = mapped_column(Enum(AppStatus), default=AppStatus.CONCEPT, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="apps")
    media: Mapped[List["AppMedia"]] = relationship("AppMedia", back_populates="app", cascade="all, delete-orphan")
    tools: Mapped[List["Tool"]] = relationship("Tool", secondary=app_tools, back_populates="apps")
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=app_tags, back_populates="apps")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="app", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="app", cascade="all, delete-orphan")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="app", cascade="all, delete-orphan")
    implementations: Mapped[List["Implementation"]] = relationship("Implementation", back_populates="app", cascade="all, delete-orphan")
    
    parent: Mapped[Optional["App"]] = relationship("App", remote_side=[id], back_populates="forks")
    forks: Mapped[List["App"]] = relationship("App", back_populates="parent")

class Implementation(Base):
    __tablename__ = "implementations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    app: Mapped["App"] = relationship("App", back_populates="implementations")
    user: Mapped["User"] = relationship("User", back_populates="implementations")

class ClaimStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"

class OwnershipClaim(Base):
    __tablename__ = "ownership_claims"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), index=True)
    claimant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), default=ClaimStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    app: Mapped["App"] = relationship("App")
    claimant: Mapped["User"] = relationship("User")

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Counter cache for performance
    score: Mapped[int] = mapped_column(default=0)

    app: Mapped["App"] = relationship("App", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")
    votes: Mapped[List["CommentVote"]] = relationship("CommentVote", back_populates="comment", cascade="all, delete-orphan")
    
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id"), nullable=True, index=True)
    parent: Mapped[Optional["Comment"]] = relationship("Comment", remote_side=[id], back_populates="replies")
    replies: Mapped[List["Comment"]] = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    app: Mapped["App"] = relationship("App", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")

class Like(Base):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    app: Mapped["App"] = relationship("App", back_populates="likes")
    user: Mapped["User"] = relationship("User", back_populates="likes")

    # Ensure a user can only like an app once
    __table_args__ = (UniqueConstraint("app_id", "user_id", name="uq_app_like"),)

class CommentVote(Base):
    __tablename__ = "comment_votes"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    value: Mapped[int] = mapped_column(default=1) # 1 for upvote, -1 for downvote
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    comment: Mapped["Comment"] = relationship("Comment", back_populates="votes")
    user: Mapped["User"] = relationship("User", back_populates="comment_votes")

    # Ensure a user can only vote on a comment once
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_vote"),)

class Collection(Base):
    __tablename__ = "collections"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    is_public: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    owner: Mapped["User"] = relationship("User", back_populates="collections")
    apps: Mapped[List["App"]] = relationship("App", secondary=collection_apps)

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


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[FeedbackType] = mapped_column(Enum(FeedbackType), default=FeedbackType.OTHER)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped["User"] = relationship("User")


class DeadAppReport(Base):
    __tablename__ = "dead_app_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.PENDING, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    app: Mapped["App"] = relationship("App")
    reporter: Mapped["User"] = relationship("User")


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IngestionJob(Base):
    """Background job for processing Reddit posts through the agent."""
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Job configuration
    subreddit: Mapped[str] = mapped_column(String(100), nullable=False, default="SideProject")
    
    # Job status
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.PENDING, index=True
    )
    
    # Progress tracking
    total_posts: Mapped[int] = mapped_column(default=0)
    processed_posts: Mapped[int] = mapped_column(default=0)
    created_apps: Mapped[int] = mapped_column(default=0)
    skipped_posts: Mapped[int] = mapped_column(default=0)
    error_count: Mapped[int] = mapped_column(default=0)
    
    # Input data: list of posts to process
    posts_data: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Results
    created_app_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    log_entries: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Cancellation support
    cancel_requested: Mapped[bool] = mapped_column(default=False, index=True)
    
    # Ownership
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_by: Mapped["User"] = relationship("User")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
