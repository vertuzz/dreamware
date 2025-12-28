from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth, users, dreams, comments, reviews, 
    likes, implementations, collections, 
    follows, notifications, tools, tags, media
)

app = FastAPI(
    title="Dreamware API",
    description="Backend for Dreamware - The Pinterest for Engineers",
    version="0.1.0"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(dreams.router, prefix="/dreams", tags=["dreams"])
app.include_router(comments.router, prefix="", tags=["comments"]) # Prefix is handled inside for dreams
app.include_router(reviews.router, prefix="", tags=["reviews"])
app.include_router(likes.router, prefix="", tags=["likes"])
app.include_router(implementations.router, prefix="", tags=["implementations"])
app.include_router(collections.router, prefix="/collections", tags=["collections"])
app.include_router(follows.router, prefix="/users", tags=["follows"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(tags.router, prefix="/tags", tags=["tags"])
app.include_router(media.router, prefix="/media", tags=["media"])

@app.get("/")
async def root():
    return {"message": "Welcome to Dreamware API"}
