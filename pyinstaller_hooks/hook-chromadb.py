"""PyInstaller hook for chromadb.

ChromaDB v0.5+ uses extensive dynamic imports via its config.get_class()
component system. PyInstaller's frozen importer cannot resolve these at
build time.  We collect every sub-module, data file and dynamic library
so that all components (SegmentAPI, SqliteDB, Posthog telemetry, …)
are available at runtime.
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

hiddenimports = collect_submodules("chromadb")
datas = collect_data_files("chromadb")
binaries = collect_dynamic_libs("chromadb")
