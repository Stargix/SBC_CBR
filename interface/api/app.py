import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Agregar raíz del proyecto al path para imports
CURRENT_DIR = Path(__file__).resolve().parent  # interface/api
INTERFACE_DIR = CURRENT_DIR.parent  # interface
PROJECT_ROOT = INTERFACE_DIR.parent  # raíz del proyecto

# Agregar tanto interface como raíz al path
for path in [str(INTERFACE_DIR), str(PROJECT_ROOT)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from api.schemas import (
    CBRRequest,
    EmbeddingsResponse,
    RetainRequest,
    RetainResponse,
    SyntheticRequest,
    TraceResponse,
)
from api.service import CBRService
from api.umap_store import UmapStore

app = FastAPI(title="Chef Digital CBR API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = CBRService()
umap_store = UmapStore()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/cases", response_model=EmbeddingsResponse)
def get_cases() -> EmbeddingsResponse:
    embeddings = umap_store.get_embeddings()
    return EmbeddingsResponse(embeddings=embeddings, total=len(embeddings))


@app.post("/request", response_model=TraceResponse)
def run_request(payload: CBRRequest) -> TraceResponse:
    trace = service.process_with_trace(payload.model_dump())
    retained_case = trace.pop("_retained_case", None)
    if retained_case:
        embedding = umap_store.upsert_case_embedding(retained_case.to_dict())
        if trace.get("retention") is not None:
            trace["retention"]["embedding"] = embedding
    return TraceResponse(**trace)


@app.post("/synthetic")
def run_synthetic(payload: SyntheticRequest) -> Dict[str, Any]:
    result = service.run_synthetic(payload.use_llm)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result


@app.post("/retain", response_model=RetainResponse)
def retain_case(payload: RetainRequest) -> RetainResponse:
    result = service.retain_from_trace(
        trace_id=payload.trace_id,
        proposal_rank=payload.proposal_rank,
        score=payload.score,
        success=payload.success,
        comments=payload.comments,
    )
    if not result.get("success"):
        return RetainResponse(
            success=False,
            message=result.get("message", "Retention failed"),
            case_id=result.get("case_id"),
        )

    embedding = None
    case = result.get("case")
    if case:
        embedding = umap_store.upsert_case_embedding(case.to_dict())

    return RetainResponse(
        success=True,
        message=result.get("message", "Retained"),
        case_id=result.get("case_id"),
        embedding=embedding,
    )


@app.post("/embeddings/transform", response_model=EmbeddingsResponse)
def transform_embeddings(payload: Dict[str, Any]) -> EmbeddingsResponse:
    embeddings = umap_store.transform_cases(payload)
    return EmbeddingsResponse(embeddings=embeddings, total=len(embeddings))
