from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.routers.auth import get_current_user
from app.models import User
from app.schemas.schemas import MediaResponse

router = APIRouter()

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

@router.post("/upload", response_model=MediaResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not settings.CLOUDINARY_CLOUD_NAME or not settings.CLOUDINARY_API_KEY or not settings.CLOUDINARY_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Cloudinary is not configured"
        )
    
    try:
        # Upload the file to Cloudinary
        result = cloudinary.uploader.upload(
            file.file,
            folder=f"vibehub/users/{current_user.id}",
            resource_type="auto"
        )
        
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not upload file: {str(e)}"
        )
