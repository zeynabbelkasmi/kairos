from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import all_activities, init_db
from .recommender import LLM_MODEL, LLM_PROVIDER, recommend
from .schemas import RecommendRequest, RecommendResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Kairos API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "activities": len(all_activities()), "llm": f"{LLM_PROVIDER}:{LLM_MODEL}"}


@app.post("/api/kairos/recommend", response_model=RecommendResponse)
async def kairos_recommend(req: RecommendRequest):
    recs, source, places_source = await recommend(req)
    return RecommendResponse(recommendations=recs, source=source, places_source=places_source)
