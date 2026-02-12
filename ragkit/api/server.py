# ragkit/api/server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
from ragkit.desktop.api import preview_ingestion

app = FastAPI()

class PreviewRequest(BaseModel):
    file_path: str
    config: dict[str, Any]

@app.get("/health")
def health_check():
    return {"ok": True}

@app.post("/api/ingestion/preview")
def api_preview_ingestion(request: PreviewRequest):
    try:
        result = preview_ingestion(request.file_path, request.config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
