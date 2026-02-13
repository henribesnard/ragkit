import pytest
from fastapi.testclient import TestClient
from ragkit.api.server import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("ragkit.api.server.FileScanner")
def test_scan_directory_endpoint(MockScanner):
    # Mock scanner behavior
    mock_instance = MockScanner.return_value
    mock_instance.scan_directory.return_value = {
        "total_files": 5,
        "files": [],
        "stats_by_type": {}
    }
    
    response = client.post("/api/ingestion/scan", json={
        "path": "/fake/path",
        "recursive": True
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 5
    mock_instance.scan_directory.assert_called_with("/fake/path", True)

def test_scan_directory_invalid_path():
    # Force an error
    with patch("ragkit.api.server.FileScanner") as MockScanner:
        MockScanner.return_value.scan_directory.side_effect = ValueError("Invalid path")
        
        response = client.post("/api/ingestion/scan", json={
            "path": "/invalid/path",
            "recursive": True
        })
        
        assert response.status_code == 400
        assert "Invalid path" in response.json()["detail"]

@patch("ragkit.api.server.preview_ingestion")
def test_preview_ingestion_endpoint(mock_preview):
    mock_preview.return_value = {
        "raw_content": "raw",
        "cleaned_content": "clean",
        "metadata": {},
        "preview_success": True
    }
    
    response = client.post("/api/ingestion/preview", json={
        "file_path": "test.pdf",
        "config": {"ocr": True}
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["preview_success"] is True
    mock_preview.assert_called_once()
