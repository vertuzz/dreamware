import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Ensure app is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.models import Base
from app.database import get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

@pytest.fixture(scope="function")
def engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    # Register and login a test user
    user_data = {"username": "testuser", "email": "test@example.com", "password": "password123"}
    client.post("/auth/register", json=user_data)
    
    # Login manually via form data
    response = client.post("/auth/login", data={"username": "testuser", "password": "password123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
