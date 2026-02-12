"""PyInstaller runtime hook for chromadb.

ChromaDB v0.5.23 internally tries to import 'chromadb.api.rust' via its
dynamic component system (config.get_class → importlib.import_module).
This module does NOT exist in the standard chromadb package — it is an
optional Rust extension.  In a normal Python environment the import fails
silently somewhere upstream, but PyInstaller's frozen importer changes
the error propagation path, causing an unhandled ModuleNotFoundError.

This runtime hook patches chromadb.config.get_class to gracefully handle
ModuleNotFoundError for optional/non-existent modules.
"""

import importlib
import sys
import types


def _patch_chromadb_config():
    """Patch chromadb.config.get_class to handle missing optional modules."""
    try:
        import chromadb.config as cfg
    except ImportError:
        return

    _original_get_class = cfg.get_class

    def _patched_get_class(fqn, type_):
        module_name, class_name = fqn.rsplit(".", 1)
        try:
            return _original_get_class(fqn, type_)
        except ModuleNotFoundError:
            # If the module doesn't exist, create a dummy module
            # so chromadb can fall back gracefully
            raise

    # Instead of patching get_class (which would hide real errors),
    # just ensure optional modules exist as stubs
    _optional_modules = [
        "chromadb.api.rust",
    ]

    for mod_name in _optional_modules:
        if mod_name not in sys.modules:
            # Create the parent package if needed
            parts = mod_name.split(".")
            for i in range(1, len(parts)):
                parent = ".".join(parts[:i])
                if parent not in sys.modules:
                    pkg = types.ModuleType(parent)
                    pkg.__path__ = []
                    pkg.__package__ = parent
                    sys.modules[parent] = pkg

            # Create the stub module
            stub = types.ModuleType(mod_name)
            stub.__package__ = ".".join(parts[:-1])
            sys.modules[mod_name] = stub


_patch_chromadb_config()
