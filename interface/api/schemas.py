from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CBRRequest(BaseModel):
    event_type: str = Field(default="FAMILIAR")
    season: str = Field(default="SPRING")
    num_guests: int = Field(default=50, ge=1)
    price_min: float = Field(default=0.0, ge=0.0)
    price_max: float = Field(default=0.0, ge=0.0)
    wants_wine: bool = False
    required_diets: List[str] = Field(default_factory=list)
    restricted_ingredients: List[str] = Field(default_factory=list)
    preferred_style: Optional[str] = None
    cultural_preference: Optional[str] = None


class SyntheticRequest(BaseModel):
    use_llm: bool = True


class EmbeddingsResponse(BaseModel):
    embeddings: List[Dict[str, Any]]
    total: int


class RetentionInfo(BaseModel):
    success: bool
    message: str
    case_id: Optional[str] = None
    proposal_rank: Optional[int] = None
    score: Optional[float] = None
    embedding: Optional[Dict[str, Any]] = None


class TraceResponse(BaseModel):
    trace_id: str
    request: Dict[str, Any]
    retrieval_results: List[Dict[str, Any]]
    proposed_menus: List[Dict[str, Any]]
    rejected_cases: List[Dict[str, Any]]
    explanations: str
    stats: Dict[str, Any]
    processing_time: float
    retention: Optional[RetentionInfo] = None


class RetainRequest(BaseModel):
    trace_id: str
    proposal_rank: int = Field(ge=1)
    score: float = Field(ge=0.0, le=5.0)
    success: bool = True
    comments: Optional[str] = None


class RetainResponse(BaseModel):
    success: bool
    message: str
    case_id: Optional[str] = None
    embedding: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    request: Dict[str, Any]
    menu_id: str
    price_satisfaction: float = Field(ge=0.0, le=5.0)
    cultural_satisfaction: float = Field(ge=0.0, le=5.0)
    flavor_satisfaction: float = Field(ge=0.0, le=5.0)
    overall_satisfaction: float = Field(ge=0.0, le=5.0)


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    case_retained: Optional[bool] = None
    case_id: Optional[str] = None
    weights_updated: Optional[Dict[str, Any]] = None
    embedding: Optional[Dict[str, Any]] = None
    retention_message: Optional[str] = None
