"""Local filesystem source loader."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable
from pathlib import Path

from ragkit.config.schema import LocalSourceConfig
from ragkit.ingestion.sources.base import BaseSourceLoader, RawDocument


class LocalSourceLoader(BaseSourceLoader):
    """Load files from the local filesystem."""

    def __init__(self, config: LocalSourceConfig):
        self.path = Path(config.path)
        self.patterns = config.patterns or ["*"]
        self.recursive = config.recursive

    def supports(self, source_config: object) -> bool:
        return isinstance(source_config, LocalSourceConfig)

    async def load(self) -> AsyncIterator[RawDocument]:
        if not self.path.exists():
            return

        files = self._iter_files()
        for file_path in files:
            file_type = self._detect_file_type(file_path)
            stat = file_path.stat()
            metadata = {
                "source_path": str(file_path),
                "file_name": file_path.name,
                "file_type": file_type,
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
            }
            content = self._read_content(file_path, file_type)
            yield RawDocument(
                content=content,
                source_path=str(file_path),
                file_type=file_type,
                metadata=metadata,
            )

    def _iter_files(self) -> Iterable[Path]:
        files: list[Path] = []
        for pattern in self.patterns:
            if self.recursive:
                files.extend(self.path.rglob(pattern))
            else:
                files.extend(self.path.glob(pattern))
        seen = set()
        ordered: list[Path] = []
        for path in files:
            if path.is_file() and path not in seen:
                seen.add(path)
                ordered.append(path)
        return ordered

    def _detect_file_type(self, path: Path) -> str:
        suffix = path.suffix.lower().lstrip(".")
        if suffix in {"md", "markdown"}:
            return "md"
        if suffix:
            return suffix
        return "unknown"

    def _read_content(self, path: Path, file_type: str) -> bytes | str:
        if file_type in {"md", "txt"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        return path.read_bytes()
