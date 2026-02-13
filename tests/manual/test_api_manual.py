import sys
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from fastapi.testclient import TestClient
    from ragkit.api.server import app
    print("Successfully imported FastAPI app")
except ImportError as e:
    print(f"Failed to import app: {e}")
    sys.exit(1)

client = TestClient(app)

def test_api():
    print("--- Testing API Endpoints ---")
    
    # Test Health
    print("Testing /health ...")
    response = client.get("/health")
    if response.status_code != 200 or response.json() != {"status": "ok"}:
        print(f"FAILURE: /health returned {response.status_code} {response.json()}")
        return False
    print("SUCCESS: /health")

    # Test Scan
    print("Testing /api/ingestion/scan ...")
    
    # Mock scanner to avoid real FS ops in API test (though we could use real FS)
    with patch("ragkit.api.server.FileScanner") as MockScanner:
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
        
        if response.status_code != 200:
            print(f"FAILURE: /scan returned {response.status_code}")
            return False
            
        data = response.json()
        if data["total_files"] != 5:
            print(f"FAILURE: Expected 5 files, got {data['total_files']}")
            return False
            
        # Verify call args
        mock_instance.scan_directory.assert_called_with("/fake/path", True)
        print("SUCCESS: /api/ingestion/scan")
        
    return True

if __name__ == "__main__":
    try:
        if test_api():
            print("ALL API TESTS PASSED")
            sys.exit(0)
        else:
            print("API TESTS FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
