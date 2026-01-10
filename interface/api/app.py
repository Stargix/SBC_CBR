import sys
import json
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    FeedbackRequest,
    FeedbackResponse,
    RetainRequest,
    RetainResponse,
    SyntheticRequest,
    TraceResponse,
)
from api.service import CBRService
from api.umap_store import umap_store

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


@app.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    result = service.process_manual_feedback(
        request_data=payload.request,
        menu_id=payload.menu_id,
        price_satisfaction=payload.price_satisfaction,
        cultural_satisfaction=payload.cultural_satisfaction,
        flavor_satisfaction=payload.flavor_satisfaction,
        overall_satisfaction=payload.overall_satisfaction,
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Feedback failed"))
    
    return FeedbackResponse(**result)


@app.get("/statistics")
def get_statistics() -> Dict[str, Any]:
    """
    Get statistics including weight evolution and simulation results
    """
    try:
        # Define paths to data files
        data_dir = PROJECT_ROOT / "data"
        results_dir = data_dir / "results"
        
        stats = {
            "learning_history": None,
            "simulation_results": None,
            "simulation_learning": None,
            "current_case_base": None,  # Estadísticas en tiempo real
            "live": None,  # Resumen compacto en vivo
        }
        
        # Try to load learning history from test results
        learning_history_path = results_dir / "learning_history_test.json"
        if learning_history_path.exists():
            with open(learning_history_path, 'r') as f:
                stats["learning_history"] = json.load(f)
        
        # Try to load LLM simulation results
        llm_sim_path = data_dir / "llm_simulation_results.json"
        if llm_sim_path.exists():
            with open(llm_sim_path, 'r') as f:
                stats["simulation_results"] = json.load(f)
        
        # Try to load LLM simulation learning
        llm_sim_learning_path = data_dir / "llm_simulation_results_learning.json"
        if llm_sim_learning_path.exists():
            with open(llm_sim_learning_path, 'r') as f:
                stats["simulation_learning"] = json.load(f)
        
        # Try groq simulation results as fallback
        groq_sim_path = data_dir / "groq_simulation_results.json"
        if groq_sim_path.exists() and not stats["simulation_results"]:
            with open(groq_sim_path, 'r') as f:
                stats["simulation_results"] = json.load(f)
        
        # Try groq simulation learning as fallback
        groq_sim_learning_path = data_dir / "groq_simulation_results_learning.json"
        if groq_sim_learning_path.exists() and not stats["simulation_learning"]:
            with open(groq_sim_learning_path, 'r') as f:
                stats["simulation_learning"] = json.load(f)
        
        # AÑADIR ESTADÍSTICAS EN TIEMPO REAL de la base de casos actual
        try:
            retention_stats = service.cbr.retainer.get_retention_statistics()
            current_weights = service.cbr.weight_learner.get_current_weights()
            total_cases = len(service.cbr.case_base.cases)
            embeddings_total = len(umap_store.get_embeddings())

            stats["current_case_base"] = {
                "retention_stats": retention_stats,
                "current_weights": {
                    "event_match": current_weights.event_match,
                    "season_match": current_weights.season_match,
                    "guest_count": current_weights.guest_count,
                    "price_range": current_weights.price_range,
                    "diet_compatibility": current_weights.diet_compatibility,
                    "cultural_match": current_weights.cultural_match,
                    "style_match": current_weights.style_match,
                },
                "total_cases": total_cases,
                "embeddings_total": embeddings_total,
                "timestamp": datetime.now().isoformat()
            }

            stats["live"] = {
                "total_cases": total_cases,
                "success_rate": retention_stats.get("success_rate"),
                "positive_cases": retention_stats.get("positive_cases"),
                "negative_cases": retention_stats.get("negative_cases"),
                "cases_by_event": retention_stats.get("cases_by_event", {}),
                "avg_feedback": retention_stats.get("avg_feedback"),
                "embeddings_total": embeddings_total,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            stats["current_case_base"] = {"error": str(e)}
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading statistics: {str(e)}")


# Mount static files for HTML reports
data_htmls_path = PROJECT_ROOT / "data" / "htmls"
if data_htmls_path.exists():
    app.mount("/reports", StaticFiles(directory=str(data_htmls_path)), name="reports")
