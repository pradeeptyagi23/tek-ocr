import pytest
from fastapi.testclient import TestClient
from main import app 
from unittest.mock import AsyncMock, patch
import aioboto3
from aiocache import caches
import json
client = TestClient(app)

@pytest.fixture
def mock_cognito_client(mocker):
    mock_client = mocker.patch("main.app.state.cognito_client")
    return mock_client

@pytest.fixture
def mock_pinecone(mocker):
    mock_index = mocker.patch("main.index")
    return mock_index

@pytest.fixture
def mock_redis(mocker):
    mock_cache = mocker.patch("aiocache.RedisCache")
    return mock_cache

@pytest.fixture
def mock_s3_client(mocker):
    session = aioboto3.Session(region_name="us-east-1")
    mock_client = mocker.patch("main.aioboto3.Session.client", return_value=session.client("s3"))
    return mock_client


@pytest.mark.asyncio
async def test_register_user(mock_cognito_client):
    response = client.post(
        "/register/",
        json={"username": "testuser", "password": "testpass", "email": "testuser@example.com"},
    )
    assert response.status_code == 200
    assert "User registered successfully" in response.json()["message"]

@pytest.mark.asyncio
async def test_login(mock_cognito_client):
    mock_cognito_client.initiate_auth.return_value = {
        'AuthenticationResult': {'AccessToken': 'dummy_token'}
    }
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "testpass"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_confirm_user(mock_cognito_client):
    response = client.post(
        "/confirm/",
        json={"username": "testuser", "confirmation_code": "123456"},
    )
    assert response.status_code == 200
    assert "User confirmed successfully" in response.json()["message"]

@pytest.mark.asyncio
async def test_upload_files(mock_s3_client):
    mock_s3_client.upload_file = AsyncMock(return_value=None)
    response = client.post(
        "/upload-files/",
        json={"file_paths": ["/path/to/file1.txt", "/path/to/file2.txt"]},
        headers={"Authorization": "Bearer dummy_token"}
    )
    assert response.status_code == 200
    assert "signed_urls" in response.json()

@pytest.mark.asyncio
async def test_process_ocr_document(mock_pinecone):
    mock_pinecone.upsert = AsyncMock(return_value=None)
    mock_pinecone.create_query_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])

    test_file = {
        "analyzeResult": {
            "pages": [{"pageNumber": 1, "words": [{"content": "test"}]}]
        }
    }

    response = client.post(
        "/upload_ocr/",
        files={"file": ("filename", json.dumps(test_file), "application/json")},
        headers={"Authorization": "Bearer dummy_token"}
    )
    assert response.status_code == 200
    assert "OCR processing and embedding completed successfully." in response.json()["status"]

@pytest.mark.asyncio
async def test_query_ocr_data(mock_pinecone, mock_redis):
    mock_redis.get = AsyncMock(return_value=None)
    mock_pinecone.query = AsyncMock(return_value={
        'matches': [
            {'score': 0.99, 'metadata': {'page_number': 1}}
        ]
    })

    response = client.post(
        "/query/",
        json={"query": "test query"},
        headers={"Authorization": "Bearer dummy_token"}
    )
    assert response.status_code == 200
    assert "score" in response.json()[0]
    assert response.json()[0]["page_number"] == 1
