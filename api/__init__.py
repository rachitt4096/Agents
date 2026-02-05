from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator import ActionOrchestrator

app = FastAPI(title="Multi-Agent Orchestrator Demo")

# Initialize orchestrator (it creates its own LLM client)
orchestrator = ActionOrchestrator()


class RunRequest(BaseModel):
    objective: str


@app.post("/run")
def run_objective(req: RunRequest):
    try:
        result = orchestrator.run(req.objective)
        return {
            "objective": req.objective,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
