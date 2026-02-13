import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class FileScanner:
    """
    Scans directories to identify supported files and generate statistics.
    """
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'pdf',
        '.docx': 'docx', 
        '.txt': 'txt',
        '.md': 'md',
        '.html': 'html',
        '.csv': 'csv'
    }

    def scan_directory(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Scans a directory and returns a list of files and statistics.
        """
        root_path = Path(path)
        if not root_path.exists() or not root_path.is_dir():
            raise ValueError(f"Invalid directory path: {path}")

        files_found: List[Dict[str, Any]] = []
        stats_by_type: Dict[str, Dict[str, int]] = {}

        # Walk through directory
        iterator = root_path.rglob('*') if recursive else root_path.glob('*')
        
        for file_path in iterator:
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    file_info = self._get_basic_file_info(file_path, root_path)
                    files_found.append(file_info)
                    
                    # Update stats
                    file_type = self.SUPPORTED_EXTENSIONS[ext]
                    if file_type not in stats_by_type:
                        stats_by_type[file_type] = {'count': 0, 'size': 0}
                    
                    stats_by_type[file_type]['count'] += 1
                    stats_by_type[file_type]['size'] += file_info['size']

        return {
            'total_files': len(files_found),
            'total_size': sum(f['size'] for f in files_found),
            'stats_by_type': stats_by_type,
            'files': files_found
        }

    def _get_basic_file_info(self, file_path: Path, root_path: Path) -> Dict[str, Any]:
        """
        Extracts basic filesystem metadata.
        """
        stat = file_path.stat()
        return {
            'name': file_path.name,
            'path': str(file_path),
            'relative_path': str(file_path.relative_to(root_path)),
            'extension': file_path.suffix.lower(),
            'type': self.SUPPORTED_EXTENSIONS.get(file_path.suffix.lower(), 'unknown'),
            'size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
