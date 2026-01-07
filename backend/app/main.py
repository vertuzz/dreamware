from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth, users, apps, comments, reviews, 
    likes, implementations, collections, 
    follows, notifications, tools, tags, media,
    ownership, feedback, agent
)
from app.core.config import settings

app = FastAPI(
    title="Show Your App API",
    description="Backend for Show Your App - The launchpad for AI-generated software",
    version="0.1.0"
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

@app.get("/")
async def root():
    return {"message": "Welcome to Show Your App API"}
