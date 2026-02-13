import sys
import os

sys.path.append(os.getcwd())

try:
    import ragkit
    print("Successfully imported ragkit")
    from ragkit.ingestion.scanner import FileScanner
    print("Successfully imported FileScanner")
except Exception as e:
    print(f"Error importing: {e}")
