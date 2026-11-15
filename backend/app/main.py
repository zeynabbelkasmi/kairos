from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .database import add_completed, init_db, list_completed
from .recommender import LLM_MODEL, LLM_PROVIDER, recommend
from .schemas import CompleteRequest, RecommendRequest, RecommendResponse


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
    return {"status": "ok", "llm": f"{LLM_PROVIDER}:{LLM_MODEL}"}


@app.post("/api/kairos/recommend", response_model=RecommendResponse)
async def kairos_recommend(req: RecommendRequest):
    recs, source, places_source, film_source = await recommend(req)
    return RecommendResponse(recommendations=recs, source=source, places_source=places_source,
                             film_source=film_source)


@app.get("/api/kairos/history")
def kairos_history():
    return [row.model_dump(mode="json") for row in list_completed()]


@app.post("/api/kairos/history")
def complete_activity(req: CompleteRequest):
    if not req.activity_id.startswith(("idea_", "film_")):
        raise HTTPException(status_code=400, detail="Seules les activités générées peuvent être enregistrées dans l'historique.")
    row = add_completed(req.activity_id, req.title, req.category_tag)
    return row.model_dump(mode="json")
