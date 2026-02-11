# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for RAGKIT Desktop backend."""

import os
import sys
from pathlib import Path

block_cipher = None

# Project root
project_root = os.path.dirname(os.path.abspath(SPEC))

# Collect data files
datas = [
    # YAML templates needed by ragkit
    (os.path.join(project_root, 'ragkit', 'templates'), os.path.join('ragkit', 'templates')),
]

# Hidden imports that PyInstaller cannot detect automatically
hiddenimports = [
    # ragkit submodules
    'ragkit.agents',
    'ragkit.config',
    'ragkit.config.defaults',
    'ragkit.config.schema',
    'ragkit.desktop',
    'ragkit.desktop.main',
    'ragkit.desktop.api',
    'ragkit.desktop.wizard_api',
    'ragkit.desktop.state',
    'ragkit.config.wizard',
    'ragkit.utils.hardware',
    'ragkit.embedding',
    'ragkit.embedding.base',
    'ragkit.ingestion',
    'ragkit.ingestion.chunkers',
    'ragkit.ingestion.parsers',
    'ragkit.ingestion.sources',
    'ragkit.ingestion.sources.base',
    'ragkit.llm',
    'ragkit.llm.providers',
    'ragkit.llm.providers.ollama_manager',
    'ragkit.onnx',
    'ragkit.retrieval',
    'ragkit.security',
    'ragkit.security.keyring',
    'ragkit.storage',
    'ragkit.storage.sqlite_store',
    'ragkit.storage.kb_manager',
    'ragkit.storage.conversation_manager',
    'ragkit.vectorstore',
    'ragkit.utils',
    # Third-party
    'litellm',
    'litellm.llms',
    'onnxruntime',
    'tokenizers',
    'huggingface_hub',
    'chromadb',
    'chromadb.telemetry.product.posthog',
    'qdrant_client',
    'unstructured',
    'rank_bm25',
    'keyring',
    'keyring.backends',
    'cryptography',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'pydantic',
    'pydantic_settings',
    'httpx',
    'httpcore',
    'structlog',
    'langdetect',
    'yaml',
    'dotenv',
    'numpy',
    'sqlite3',
]

a = Analysis(
    [os.path.join(project_root, 'ragkit', 'desktop', 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy modules not needed at runtime
        'gradio',
        'matplotlib',
        'tkinter',
        'test',
        'unittest',
        'pytest',
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ragkit-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,
)
