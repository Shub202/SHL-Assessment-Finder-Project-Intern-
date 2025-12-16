from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import os
import uvicorn

app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="API for recommending SHL assessments based on job descriptions and queries",
    version="1.0.0"
)

model = None
catalog_df = None
corpus = None
corpus_embeddings = None

@app.on_event("startup")
def startup_event():
    global model, catalog_df, corpus, corpus_embeddings
    
    print("Loading models and data...")
    
    from query_functions import initialize_models
    catalog_df, corpus, model, corpus_embeddings, _ = initialize_models()
    
    print("Startup complete!")

class QueryRequest(BaseModel):
    query: str

class Assessment(BaseModel):
    assessment_name: str
    url: str
    adaptive_support: str
    description: str
    duration: int
    remote_support: str
    test_type: List[str]
    skills: List[str]

class RecommendationResponse(BaseModel):
    recommended_assessments: List[Assessment]

@app.get("/")
def root():
    return {
        "message": "SHL Assessment Recommendation API",
        "endpoints": [
            {"path": "/recommend", "method": "POST", "description": "Get assessment recommendations"},
            {"path": "/health", "method": "GET", "description": "Health check"}
        ],
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/recommend", response_model=RecommendationResponse)
def recommend_assessments(request: QueryRequest):
    try:
        from query_functions import query_handling_using_LLM_updated
        
        df = query_handling_using_LLM_updated(request.query)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No assessments found.")
        
        results = []
        
        for _, row in df.iterrows():
            duration_val = row.get("Duration", 30)
            if isinstance(duration_val, str):
                import re
                match = re.search(r'(\d+)', duration_val)
                duration_val = int(match.group(1)) if match else 30
            else:
                duration_val = int(duration_val) if pd.notna(duration_val) else 30
            
            test_type = row.get("Test Type", "General")
            if isinstance(test_type, str):
                test_type_list = [t.strip() for t in test_type.split(",")]
            else:
                test_type_list = [str(test_type)]
            
            skills = row.get("Skills", "")
            if isinstance(skills, str):
                skills_list = [s.strip() for s in skills.split(",")]
            else:
                skills_list = [str(skills)]
            
            results.append({
                "assessment_name": str(row.get("Assessment Name", "")),
                "url": str(row.get("URL", "")),
                "adaptive_support": str(row.get("Adaptive/IRT", "No")),
                "description": str(row.get("Description", "")),
                "duration": duration_val,
                "remote_support": str(row.get("Remote Testing Support", "No")),
                "test_type": test_type_list,
                "skills": skills_list
            })
        
        return {"recommended_assessments": results}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
