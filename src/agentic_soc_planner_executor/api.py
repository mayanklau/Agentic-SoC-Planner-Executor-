import uvicorn
from fastapi import FastAPI

from agentic_soc_planner_executor.models import ExecutionRecord, RawAlert, ResponsePlan
from agentic_soc_planner_executor.orchestrator import AgenticSOCService


def create_app() -> FastAPI:
    service = AgenticSOCService()
    app = FastAPI(
        title="Agentic SOC Planner Executor",
        version="0.1.0",
        description="Planner/executor backend for graph-grounded, risk-aware SOC automation.",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/incidents/plan", response_model=ResponsePlan)
    def plan_incident(alert: RawAlert) -> ResponsePlan:
        return service.plan_alert(alert)

    @app.post("/incidents/execute", response_model=ExecutionRecord)
    def execute_incident(alert: RawAlert) -> ExecutionRecord:
        return service.handle_alert(alert)

    return app


def run() -> None:
    uvicorn.run(
        "agentic_soc_planner_executor.api:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
    )
