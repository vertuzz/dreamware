import pytest
from unittest.mock import patch
from io import BytesIO

def test_upload_image_success(client, auth_headers):
    # Mock cloudinary.uploader.upload
    mock_response = {
        "secure_url": "https://res.cloudinary.com/demo/image/upload/v1234567890/sample.jpg",
        "public_id": "sample"
    }
    
    with patch("cloudinary.uploader.upload", return_value=mock_response):
        # Create a dummy image file
        file_content = b"fake image content"
        file = BytesIO(file_content)
        
        response = client.post(
            "/media/upload",
            headers=auth_headers,
            files={"file": ("test.jpg", file, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == mock_response["secure_url"]
        assert data["public_id"] == mock_response["public_id"]

def test_upload_image_unauthorized(client):
    # Test upload without auth headers
    file_content = b"fake image content"
    file = BytesIO(file_content)
    
    response = client.post(
        "/media/upload",
        files={"file": ("test.jpg", file, "image/jpeg")}
    )
    
    assert response.status_code == 401

def test_upload_image_cloudinary_error(client, auth_headers):
    # Mock cloudinary.uploader.upload to raise an exception
    with patch("cloudinary.uploader.upload", side_effect=Exception("Cloudinary error")):
        file_content = b"fake image content"
        file = BytesIO(file_content)
        
        response = client.post(
            "/media/upload",
            headers=auth_headers,
            files={"file": ("test.jpg", file, "image/jpeg")}
        )
        
        assert response.status_code == 400
        assert "Could not upload file" in response.json()["detail"]
