import sys
import os
import shutil
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from ragkit.ingestion.scanner import FileScanner
    print("Successfully imported FileScanner")
except ImportError as e:
    print(f"Failed to import FileScanner: {e}")
    sys.exit(1)

def test_scanner():
    # Create temp dir
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create files
        (tmp_path / "doc1.pdf").touch()
        (tmp_path / "note.txt").write_text("content", encoding="utf-8")
        
        # Subfolder
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "doc2.docx").touch()
        
        scanner = FileScanner()
        print(f"Supported extensions: {scanner.SUPPORTED_EXTENSIONS}")
        
        # Test Recursive
        print("Testing recursive scan...")
        result = scanner.scan_directory(str(tmp_path), recursive=True)
        print(f"Recursive result: {result}")
        
        if result["total_files"] != 3:
            print(f"FAILURE: Expected 3 files, got {result['total_files']}")
            return False
            
        # Test Non-Recursive
        print("Testing non-recursive scan...")
        result = scanner.scan_directory(str(tmp_path), recursive=False)
        print(f"Non-recursive result: {result}")
        
        if result["total_files"] != 2: # doc1.pdf, note.txt
            print(f"FAILURE: Expected 2 files, got {result['total_files']}")
            return False
            
        print("SUCCESS: specific tests passed")
        return True

if __name__ == "__main__":
    try:
        if test_scanner():
            print("ALL MANUAL TESTS PASSED")
            sys.exit(0)
        else:
            print("TESTS FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
