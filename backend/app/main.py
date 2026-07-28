from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import agent, courses, plan, progress, requirements

app = FastAPI(title="AI Course Compass API")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(requirements.router)
app.include_router(progress.router)
app.include_router(agent.router)
app.include_router(plan.router)


@app.get("/health")
def health():
    return {"status": "ok"}
