from fastapi import APIRouter, HTTPException, Depends
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from app.core.config import settings
from app.routers.auth import get_current_user
from app.models import User
from app.schemas.schemas import MediaResponse, PresignedUrlRequest
import uuid

router = APIRouter()

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        endpoint_url=settings.S3_ENDPOINT_URL,
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}
        )
    )

@router.post("/presigned-url", response_model=MediaResponse)
async def get_presigned_url(
    request: PresignedUrlRequest,
    current_user: User = Depends(get_current_user),
    s3_client = Depends(get_s3_client)
):
    if not settings.S3_BUCKET or not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise HTTPException(
            status_code=500,
            detail="S3 is not configured"
        )
    
    try:
        # Generate a unique filename
        file_extension = request.filename.split(".")[-1] if "." in request.filename else "jpg"
        file_key = f"users/{current_user.id}/{uuid.uuid4()}.{file_extension}"
        
        # Generate presigned URL for PUT request
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.S3_BUCKET,
                'Key': file_key,
                'ContentType': request.content_type
            },
            ExpiresIn=3600
        )
        
        # Construct the download URL
        if settings.S3_ENDPOINT_URL:
            # For S3-compatible services like MinIO or DigitalOcean Spaces
            # Remove trailing slash from endpoint if present
            base_url = settings.S3_ENDPOINT_URL.rstrip('/')
            download_url = f"{base_url}/{settings.S3_BUCKET}/{file_key}"
        else:
            # Standard AWS S3 URL
            download_url = f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
        
        return {
            "upload_url": presigned_url,
            "download_url": download_url,
            "file_key": file_key
        }
    except ClientError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not generate presigned URL: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error: {str(e)}"
        )
