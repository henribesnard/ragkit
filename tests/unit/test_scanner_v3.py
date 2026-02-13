import pytest
import os
from pathlib import Path
from ragkit.ingestion.scanner import FileScanner

@pytest.fixture
def temp_scan_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    # Create root files
    (tmp_path / "doc1.pdf").touch()
    (tmp_path / "note.txt").write_text("content")
    (tmp_path / "dataset.csv").touch()
    (tmp_path / "ignored.exe").touch()

    # Create subfolder
    sub = tmp_path / "subfolder"
    sub.mkdir()
    (sub / "doc2.docx").touch()
    (sub / "script.py").touch() # Not in default supported list?
    
    return tmp_path

def test_scanner_initialization():
    scanner = FileScanner()
    assert ".pdf" in scanner.SUPPORTED_EXTENSIONS
    assert "pdf" == scanner.SUPPORTED_EXTENSIONS[".pdf"]

def test_scan_recursive(temp_scan_dir):
    scanner = FileScanner()
    result = scanner.scan_directory(str(temp_scan_dir), recursive=True)
    
    assert result["total_files"] == 3 # pdf, txt, csv, docx (wait, docx in subfolder)
    # Supported: pdf, docx, txt, md, html, csv
    # doc1.pdf (yes), note.txt (yes), dataset.csv (yes), ignored.exe (no)
    # subfolder/doc2.docx (yes), subfolder/script.py (no)
    # Total should be 4
    
    assert result["total_files"] == 4
    
    stats = result["stats_by_type"]
    assert stats["pdf"]["count"] == 1
    assert stats["txt"]["count"] == 1
    assert stats["csv"]["count"] == 1
    assert stats["docx"]["count"] == 1
    
    filenames = [f["name"] for f in result["files"]]
    assert "doc1.pdf" in filenames
    assert "doc2.docx" in filenames
    assert "ignored.exe" not in filenames

def test_scan_non_recursive(temp_scan_dir):
    scanner = FileScanner()
    result = scanner.scan_directory(str(temp_scan_dir), recursive=False)
    
    # Should only find root files: doc1.pdf, note.txt, dataset.csv
    assert result["total_files"] == 3
    filenames = [f["name"] for f in result["files"]]
    assert "doc1.pdf" in filenames
    assert "doc2.docx" not in filenames

def test_invalid_path():
    scanner = FileScanner()
    with pytest.raises(ValueError):
        scanner.scan_directory("/path/to/non/existent/directory")
