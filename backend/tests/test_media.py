import pytest
from io import BytesIO
from app.core.config import settings
from moto import mock_aws
import boto3
import os

@pytest.fixture
def s3_setup():
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="vibehub")
        yield s3

@pytest.mark.asyncio
async def test_get_presigned_url_success(client, auth_headers, s3_setup):
    # Mock settings for test
    settings.S3_BUCKET = "vibehub"
    settings.AWS_ACCESS_KEY_ID = "testing"
    settings.AWS_SECRET_ACCESS_KEY = "testing"
    settings.AWS_REGION = "us-east-1"

    response = await client.post(
        "/media/presigned-url",
        headers=auth_headers,
        json={"filename": "test.jpg", "content_type": "image/jpeg"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "upload_url" in data
    assert "download_url" in data
    assert "file_key" in data
    assert "vibehub.s3.us-east-1.amazonaws.com" in data["download_url"]
    assert data["file_key"].startswith("users/")
    assert "X-Amz-Algorithm" in data["upload_url"]

@pytest.mark.asyncio
async def test_get_presigned_url_unauthorized(client):
    # Test without auth headers
    response = await client.post(
        "/media/presigned-url",
        json={"filename": "test.jpg", "content_type": "image/jpeg"}
    )
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_presigned_url_s3_not_configured(client, auth_headers):
    # Temporarily unset settings
    old_bucket = settings.S3_BUCKET
    settings.S3_BUCKET = None
    
    try:
        response = await client.post(
            "/media/presigned-url",
            headers=auth_headers,
            json={"filename": "test.jpg", "content_type": "image/jpeg"}
        )
        
        assert response.status_code == 500
        assert "S3 is not configured" in response.json()["detail"]
    finally:
        settings.S3_BUCKET = old_bucket
