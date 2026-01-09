import asyncio
import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, or_, delete
from sqlalchemy.orm import attributes

from app.routers import (
    auth, users, apps, comments, reviews, 
    likes, implementations, collections, 
    follows, notifications, tools, tags, media,
    ownership, feedback, agent, og
)
from app.routers.jobs import router as jobs_router
from app.core.config import settings
from app.core.logfire_config import configure_logfire
from app.database import AsyncSessionLocal
from app.models import IngestionJob, JobStatus, User, App
from app.agent.agent import run_agent
from app.agent.deps import AgentDeps

# Initialize Logfire observability (sends data when LOGFIRE_TOKEN is set)
configure_logfire()

logger = logging.getLogger(__name__)

# URL pattern to extract URLs from post body
URL_PATTERN = re.compile(r'https?://[^\s\)\]\>\"\']+')

# Global flag to stop worker on shutdown
_worker_running = False


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from text."""
    if not text:
        return []
    urls = URL_PATTERN.findall(text)
    cleaned = []
    for url in urls:
        url = url.rstrip(".,;:!?")
        if "reddit.com" in url or "redd.it" in url:
            continue
        if "imgur.com" in url or "i.redd.it" in url:
            continue
        cleaned.append(url)
    return cleaned


def build_agent_prompt(post: dict) -> str:
    """Build the agent prompt for a Reddit post."""
    title = post.get("title", "")
    selftext = post.get("selftext", "")
    permalink = post.get("permalink", "")
    if not permalink.startswith("http"):
        permalink = f"https://reddit.com{permalink}"
    
    return f"""Evaluate this Reddit post from r/SideProject. 

**Decision criteria:**
- If it showcases a real app or project worth adding to our platform, create an app listing.
- SKIP if it's: spam, a question/discussion, hiring post, self-promotion without an app, or low-quality content.
- If you decide to create an app, use post_url="{permalink}" to track the source.

**Post Title:** {title}

**Post Content:**
{selftext}

If you create an app listing, make sure to:
1. Visit the app URL and take screenshots
2. Check for duplicates first using search_apps
3. Write compelling title, prompt_text, and prd_text
4. Set appropriate tags and tools
"""


async def check_post_processed(db, post_url: str) -> bool:
    """Check if a post has already been processed."""
    result = await db.execute(select(App.id).filter(App.post_url == post_url).limit(1))
    return result.scalar() is not None


async def check_urls_exist(db, urls: list[str]) -> list[str]:
    """Check which URLs already exist as app_url in the database."""
    if not urls:
        return []
    filters = [App.app_url.ilike(f"%{url}%") for url in urls]
    result = await db.execute(select(App.app_url).filter(or_(*filters)))
    existing = result.scalars().all()
    return existing


async def process_single_post(db, user_data: dict, post: dict) -> dict:
    """Process a single post through the agent."""
    permalink = post.get("permalink", "")
    if not permalink.startswith("http"):
        permalink = f"https://reddit.com{permalink}"
    selftext = post.get("selftext", "")
    
    # Get URLs from extracted_urls or extract from selftext
    urls = post.get("extracted_urls", []) or extract_urls(selftext)
    
    if not urls:
        return {"skipped": True, "reason": "no_urls"}
    
    if await check_post_processed(db, permalink):
        return {"skipped": True, "reason": "post_exists"}
    
    existing_urls = await check_urls_exist(db, urls)
    if existing_urls:
        return {"skipped": True, "reason": "url_exists", "existing": existing_urls}
    
    prompt = build_agent_prompt(post)
    deps = AgentDeps(
        db=db,
        user_id=user_data["id"],
        username=user_data["username"],
        is_admin=user_data["is_admin"],
    )
    
    result = await run_agent(prompt, deps)
    return result


async def process_job(job_id: int):
    """Process a single ingestion job."""
    async with AsyncSessionLocal() as db:
        # Fetch job
        result = await db.execute(select(IngestionJob).filter(IngestionJob.id == job_id))
        job = result.scalar()
        
        if not job or job.status != JobStatus.PENDING:
            return
        
        # Helper to append to log and mark as modified
        def add_log(msg: str):
            if job.log_entries is None:
                job.log_entries = []
            job.log_entries = job.log_entries + [msg]  # Create new list to trigger change detection
        
        # Mark as running
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        if job.log_entries is None:
            job.log_entries = []
        if job.created_app_ids is None:
            job.created_app_ids = []
        await db.commit()
        
        # Get admin user
        result = await db.execute(select(User).filter(User.id == job.created_by_id))
        user = result.scalar()
        
        if not user:
            job.status = JobStatus.FAILED
            job.error_message = "Creator user not found"
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin,
        }
        
        posts = job.posts_data or []
        add_log(f"Starting processing of {len(posts)} posts")
        await db.commit()
        
        try:
            for i, post in enumerate(posts):
                # Check for cancellation
                await db.refresh(job)
                if job.cancel_requested:
                    job.status = JobStatus.CANCELLED
                    add_log(f"Cancelled at post {i+1}/{len(posts)}")
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    return
                
                title = post.get("title", "Unknown")[:60]
                add_log(f"[{i+1}/{len(posts)}] Processing: {title}...")
                await db.commit()
                
                try:
                    result = await process_single_post(db, user_data, post)
                    
                    if result.get("skipped"):
                        job.skipped_posts += 1
                        add_log(f"  Skipped: {result.get('reason')}")
                    elif result.get("success"):
                        app_ids = result.get("app_ids", [])
                        job.created_apps += len(app_ids)
                        job.created_app_ids = job.created_app_ids + app_ids  # New list for change detection
                        add_log(f"  Created apps: {app_ids}")
                    else:
                        job.error_count += 1
                        error = result.get("error", "Unknown error")[:200]
                        add_log(f"  Error: {error}")
                        
                except Exception as e:
                    job.error_count += 1
                    add_log(f"  Exception: {str(e)[:200]}")
                    logger.exception(f"Error processing post in job {job_id}")
                
                job.processed_posts += 1
                await db.commit()
            
            job.status = JobStatus.COMPLETED
            add_log(f"Completed. Created {job.created_apps} apps, skipped {job.skipped_posts}, errors {job.error_count}")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)[:500]
            add_log(f"Job failed: {str(e)[:200]}")
            logger.exception(f"Job {job_id} failed")
        
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()


async def cleanup_old_jobs():
    """Delete jobs older than 30 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(IngestionJob).where(IngestionJob.created_at < cutoff)
        )
        if result.rowcount > 0:
            await db.commit()
            logger.info(f"Cleaned up {result.rowcount} old ingestion jobs")


async def job_worker():
    """Background worker that polls for and processes pending jobs."""
    global _worker_running
    _worker_running = True
    logger.info("Ingestion job worker started")
    
    cleanup_counter = 0
    
    while _worker_running:
        try:
            # Poll for pending jobs
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(IngestionJob.id)
                    .filter(IngestionJob.status == JobStatus.PENDING)
                    .order_by(IngestionJob.created_at)
                    .limit(1)
                )
                job_id = result.scalar()
            
            if job_id:
                logger.info(f"Processing job {job_id}")
                await process_job(job_id)
            
            # Cleanup old jobs every ~5 minutes (60 poll cycles * 5 seconds)
            cleanup_counter += 1
            if cleanup_counter >= 60:
                cleanup_counter = 0
                await cleanup_old_jobs()
            
        except Exception as e:
            logger.exception(f"Error in job worker: {e}")
        
        await asyncio.sleep(5)  # Poll every 5 seconds
    
    logger.info("Ingestion job worker stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup: launch background worker
    worker_task = asyncio.create_task(job_worker())
    
    yield
    
    # Shutdown: stop worker
    global _worker_running
    _worker_running = False
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Show Your App API",
    description="Backend for Show Your App - The launchpad for AI-generated software",
    version="0.1.0",
    lifespan=lifespan,
)

# Set CORS origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Newest-App-Id"],
)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(apps.router, prefix="/apps", tags=["apps"])
app.include_router(comments.router, prefix="", tags=["comments"]) # Prefix is handled inside for apps
app.include_router(reviews.router, prefix="", tags=["reviews"])
app.include_router(likes.router, prefix="", tags=["likes"])
app.include_router(implementations.router, prefix="", tags=["implementations"])
app.include_router(collections.router, prefix="/collections", tags=["collections"])
app.include_router(follows.router, prefix="/users", tags=["follows"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(tags.router, prefix="/tags", tags=["tags"])
app.include_router(media.router, prefix="/media", tags=["media"])
app.include_router(ownership.router, tags=["ownership"])
app.include_router(feedback.router, tags=["feedback"])
app.include_router(agent.router, tags=["agent"])
app.include_router(og.router, prefix="/og", tags=["og"])
app.include_router(jobs_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Show Your App API"}
