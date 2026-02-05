"""
FastAPI Application - REST API for Multi-Agent Orchestrator
REAL execution + live logs + Streamlit compatible
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
from pathlib import Path

from orchestrator.orchestrator import ActionOrchestrator
from config.settings import settings

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "runtime.log"

logger.add(
    LOG_FILE,
    rotation="1 MB",
    level="INFO",
    enqueue=True,
    format="{time:HH:mm:ss} | {level} | {message}"
)

logger.info("Logging initialized")

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Multi-Agent Orchestrator API",
    description="Autonomous multi-agent system with real execution",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Orchestrator
# -----------------------------------------------------------------------------
orchestrator = ActionOrchestrator()

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class RunRequest(BaseModel):
    objective: str


class RunResponse(BaseModel):
    objective: str
    result: str
    completed_at: datetime


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "multi-agent-orchestrator",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# -----------------------------------------------------------------------------
# 🔥 MAIN ENDPOINT (STREAMLIT USES THIS)
# -----------------------------------------------------------------------------
@app.post("/run", response_model=RunResponse)
def run_objective(req: RunRequest):
    """
    Execute an objective using the multi-agent system
    """
    if not req.objective.strip():
        raise HTTPException(status_code=400, detail="Objective cannot be empty")

    logger.info("=" * 80)
    logger.info(f"NEW OBJECTIVE RECEIVED: {req.objective}")
    logger.info("=" * 80)

    try:
        objective = orchestrator.execute_objective(req.objective)

        logger.success(f"OBJECTIVE FINISHED: {objective.status}")

        return RunResponse(
            objective=req.objective,
            result=objective.final_result,
            completed_at=objective.completed_at
        )

    except Exception as e:
        logger.exception("Execution failed")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# 🖥 LIVE LOG STREAM (FOR STREAMLIT CONSOLE)
# -----------------------------------------------------------------------------
@app.get("/logs/stream", response_class=PlainTextResponse)
def stream_logs():
    try:
        with open("logs/runtime.log", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Log file not found yet."

# -----------------------------------------------------------------------------
# Stats (optional)
# -----------------------------------------------------------------------------
@app.get("/stats")
def stats():
    return orchestrator.get_stats()


# -----------------------------------------------------------------------------
# Startup / Shutdown
# -----------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    logger.info("🚀 Multi-Agent Orchestrator API started")
    logger.info(f"API running on http://127.0.0.1:8000")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("🛑 Multi-Agent Orchestrator API stopped")


# -----------------------------------------------------------------------------
# Local run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )