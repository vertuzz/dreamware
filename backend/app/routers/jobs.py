"""Admin-only router for managing ingestion jobs."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, IngestionJob, JobStatus
from app.routers.auth import require_admin


router = APIRouter(prefix="/jobs", tags=["jobs"])


# === Schemas ===

class RedditPost(BaseModel):
    """A single Reddit post to process."""
    title: str
    selftext: str
    permalink: str
    score: int = 0
    created_utc: float = 0
    extracted_urls: list[str] = []


class IngestionJobCreate(BaseModel):
    """Request body for creating an ingestion job."""
    posts: list[RedditPost]
    subreddit: str = "SideProject"


class IngestionJobResponse(BaseModel):
    """Response for a single job."""
    id: int
    status: JobStatus
    subreddit: str
    total_posts: int
    processed_posts: int
    created_apps: int
    skipped_posts: int
    error_count: int
    created_app_ids: list[int] | None
    error_message: str | None
    log_entries: list[str] | None
    cancel_requested: bool
    created_by_id: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class IngestionJobListResponse(BaseModel):
    """Response for listing jobs."""
    jobs: list[IngestionJobResponse]
    total: int


class JobCreateResponse(BaseModel):
    """Response after creating a job."""
    job_id: int
    status: JobStatus
    message: str


# === Endpoints ===

@router.post("/ingestion", response_model=JobCreateResponse)
async def create_ingestion_job(
    request: IngestionJobCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Create a new ingestion job to process Reddit posts.
    
    Admin-only endpoint. Accepts a list of Reddit posts and queues them
    for background processing by the agent.
    
    Returns the job ID which can be used to check status.
    """
    if not request.posts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No posts provided",
        )
    
    # Convert posts to JSON-serializable format
    posts_data = [post.model_dump() for post in request.posts]
    
    # Create job
    job = IngestionJob(
        subreddit=request.subreddit,
        status=JobStatus.PENDING,
        total_posts=len(posts_data),
        processed_posts=0,
        created_apps=0,
        skipped_posts=0,
        error_count=0,
        posts_data=posts_data,
        created_app_ids=[],
        log_entries=[],
        cancel_requested=False,
        created_by_id=admin_user.id,
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        message=f"Job created with {len(posts_data)} posts. Processing will begin shortly.",
    )


@router.get("/ingestion", response_model=IngestionJobListResponse)
async def list_ingestion_jobs(
    status_filter: Optional[JobStatus] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    List ingestion jobs.
    
    Admin-only endpoint. Optionally filter by status.
    """
    query = select(IngestionJob).order_by(desc(IngestionJob.created_at))
    
    if status_filter:
        query = query.filter(IngestionJob.status == status_filter)
    
    # Get total count
    count_query = select(IngestionJob)
    if status_filter:
        count_query = count_query.filter(IngestionJob.status == status_filter)
    result = await db.execute(count_query)
    total = len(result.scalars().all())
    
    # Get paginated results
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return IngestionJobListResponse(
        jobs=[IngestionJobResponse.model_validate(job) for job in jobs],
        total=total,
    )


@router.get("/ingestion/{job_id}", response_model=IngestionJobResponse)
async def get_ingestion_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Get details of a specific ingestion job.
    
    Admin-only endpoint.
    """
    result = await db.execute(
        select(IngestionJob).filter(IngestionJob.id == job_id)
    )
    job = result.scalar()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    return IngestionJobResponse.model_validate(job)


@router.post("/ingestion/{job_id}/cancel")
async def cancel_ingestion_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Request cancellation of a running or pending job.
    
    Admin-only endpoint. Sets the cancel_requested flag.
    The worker will stop processing after completing the current post.
    """
    result = await db.execute(
        select(IngestionJob).filter(IngestionJob.id == job_id)
    )
    job = result.scalar()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status {job.status.value}",
        )
    
    job.cancel_requested = True
    await db.commit()
    
    return {
        "job_id": job_id,
        "cancel_requested": True,
        "message": "Cancellation requested. Job will stop after current post.",
    }
