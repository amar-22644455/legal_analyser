import os
import shutil
import sys
from typing import Any, Optional

import fitz
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.rag.embedder import create_embeddings
from app.rag.rag_pipeline import RAGPipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DOCS_DIR = os.path.join(BASE_DIR, "docs")
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "embeddings")
UI_DIR = os.path.join(BASE_DIR, "ui")
DIST_DIR = os.path.join(UI_DIR, "dist")
DIST_ASSETS_DIR = os.path.join(DIST_DIR, "assets")

# --- Constants and State ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
DIST_DIR = os.path.join(BASE_DIR, "ui", "dist")
DIST_ASSETS_DIR = os.path.join(DIST_DIR, "assets")
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"}

# In-memory state. In a real app, you'd use a database or other persistent storage.
_state: dict[str, Any] = {
    "rag": None,
    "uploaded_documents": [],
}

app = FastAPI(title="Legal Risk Analysis AI")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(DIST_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=DIST_ASSETS_DIR), name="assets")

# Global state to hold our pipeline and document list
_state: dict[str, Any] = {
    "rag": None,
    "uploaded_documents": [],
}

# --- Pydantic Models for API Requests ---
class QueryPayload(BaseModel):
    query: str
    target_file: Optional[str] = None
    is_chat: Optional[bool] = True

class ComparePayload(BaseModel):
    query: str
    file_a: str
    file_b: str


# --- Helper Functions ---
def _ensure_dirs() -> None:
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

def _clear_docs_and_embeddings() -> None:
    if os.path.exists(DOCS_DIR):
        shutil.rmtree(DOCS_DIR)
    if os.path.exists(EMBEDDINGS_DIR):
        shutil.rmtree(EMBEDDINGS_DIR)
    _ensure_dirs()


# --- API Routes ---

@app.get("/api/status")
def status() -> dict[str, Any]:
    return {
        "ok": True,
        "uploadedDocuments": _state.get("uploaded_documents", []),
    }

@app.post("/api/reset")
def reset() -> dict[str, Any]:
    _clear_docs_and_embeddings()
    _state["rag"] = None
    _state["uploaded_documents"] = []
    return {"ok": True}

@app.post("/api/upload")
async def upload_documents(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="No files received.")

    # We clear the previous embeddings but keep the docs if we want to add to them.
    # For a fresh workspace on every upload, we clear both.
    if os.path.exists(EMBEDDINGS_DIR):
        shutil.rmtree(EMBEDDINGS_DIR)
    _ensure_dirs()

    saved_count = 0
    new_docs = []

    for upload in files:
        filename = upload.filename or "uploaded_file"
        suffix = os.path.splitext(filename)[1].lower()
        
        if suffix not in ALLOWED_EXTENSIONS:
            continue

        destination = os.path.join(DOCS_DIR, filename)
        with open(destination, "wb") as out:
            out.write(await upload.read())

        new_docs.append(filename)
        saved_count += 1

    if saved_count == 0:
        raise HTTPException(status_code=400, detail="No supported files uploaded.")

    # 1. Create the new dictionary-based embeddings
    created = create_embeddings()
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create embeddings from uploaded documents.")

    # 2. Initialize the new RAG Pipeline
    pipeline = RAGPipeline()
    _state["rag"] = pipeline
    
    # 3. Update active documents
    combined_docs = _state.get("uploaded_documents", []) + new_docs
    _state["uploaded_documents"] = list(dict.fromkeys(combined_docs))

    # 4. Generate the individual summaries automatically!
    summaries = pipeline.generate_summaries(new_docs)

    return {
        "ok": True,
        "uploaded": saved_count,
        "uploadedDocuments": _state["uploaded_documents"],
        "summaries": summaries # The UI can use this to instantly populate the dashboard
    }

@app.post("/api/query")
async def query_endpoint(payload: QueryPayload) -> dict[str, Any]:
    """Handles standard chat and single-document analysis."""
    rag: RAGPipeline = _state.get("rag")
    if not rag:
        raise HTTPException(status_code=400, detail="Upload documents first.")
    
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Target file is exactly what we pass to source_filter in the pipeline
    target = payload.target_file if payload.target_file != "All Documents" else None

    try:
        result = rag.query_document(
            query=payload.query, 
            target_file=target, 
            is_chat=payload.is_chat
        )
        return {"ok": True, "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/compare")
async def compare_endpoint(payload: ComparePayload) -> dict[str, Any]:
    """Handles strictly the two-document comparison mode."""
    rag: RAGPipeline = _state.get("rag")
    if not rag:
        raise HTTPException(status_code=400, detail="Upload documents first.")

    if not payload.file_a or not payload.file_b:
        raise HTTPException(status_code=400, detail="Comparison requires exactly two files.")

    try:
        result = rag.compare_documents(
            query=payload.query, 
            file_a=payload.file_a, 
            file_b=payload.file_b
        )
        return {"ok": True, "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# --- SPA Fallback & Serving ---
@app.get("/")
def index() -> FileResponse:
    dist_index = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    return FileResponse(os.path.join(UI_DIR, "index.html"))

@app.get("/{full_path:path}")
def spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")

    candidate_dist = os.path.join(DIST_DIR, full_path)
    if os.path.exists(candidate_dist) and os.path.isfile(candidate_dist):
        return FileResponse(candidate_dist)

    candidate_ui = os.path.join(UI_DIR, full_path)
    if os.path.exists(candidate_ui) and os.path.isfile(candidate_ui):
        return FileResponse(candidate_ui)

    dist_index = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)

    return FileResponse(os.path.join(UI_DIR, "index.html"))

if os.path.exists(DIST_DIR):
    @app.get("/", response_class=FileResponse)
    async def read_index():
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("legal_dashboard:app", host="127.0.0.1", port=8000, reload=True)