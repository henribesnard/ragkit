import pytest
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

# Run pytest on the specific test file
retcode = pytest.main(["-v", "tests/unit/test_scanner_v3.py"])

print(f"Pytest exited with code: {retcode}")
