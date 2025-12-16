from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from query_functions import get_engine
import uvicorn

app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="AI-powered assessment recommendations for hiring managers",
    version="1.0.0"
)


class RecommendationRequest(BaseModel):
    query: Optional[str] = None
    url: Optional[str] = None
    max_duration: Optional[int] = None
    test_types: Optional[List[str]] = None
    remote_only: bool = False
    top_k: int = 10


class HealthResponse(BaseModel):
    status: str
    catalog_size: int
    ai_enabled: bool


@app.get("/")
def root():
    return {"message": "SHL Assessment Recommendation API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
def health_check():
    engine = get_engine()
    stats = engine.get_catalog_stats()
    return HealthResponse(
        status="healthy",
        catalog_size=stats['total_assessments'],
        ai_enabled=engine.gemini_client is not None
    )


@app.post("/recommend")
def get_recommendations(request: RecommendationRequest):
    if not request.query and not request.url:
        raise HTTPException(
            status_code=400,
            detail="Either 'query' or 'url' must be provided"
        )
    
    engine = get_engine()
    results = engine.get_recommendations(
        query=request.query,
        url=request.url,
        max_duration=request.max_duration,
        test_types=request.test_types,
        remote_only=request.remote_only,
        top_k=request.top_k
    )
    
    return results


@app.get("/test-types")
def get_test_types():
    engine = get_engine()
    return {"test_types": engine.get_test_types()}


@app.get("/stats")
def get_stats():
    engine = get_engine()
    return engine.get_catalog_stats()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
