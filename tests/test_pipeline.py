from fastapi.testclient import TestClient

from agentic_soc_planner_executor.api import create_app
from agentic_soc_planner_executor.config import Settings
from agentic_soc_planner_executor.knowledge_store import InMemoryKnowledgeStore
from agentic_soc_planner_executor.models import ActionType, ApprovalState, RawAlert
from agentic_soc_planner_executor.orchestrator import AgenticSOCService


def kerberos_alert() -> RawAlert:
    return RawAlert(
        source="siem",
        event_type="Kerberos TGT Request",
        source_user="user123",
        source_host="ws-fin-27",
        destination_host="srv-fin-03",
        result="Success",
        severity="high",
        attributes={"process": "powershell.exe", "geo_velocity": "unusual"},
    )


def test_planner_separates_feasible_and_rejected_hypotheses() -> None:
    service = AgenticSOCService()

    plan = service.plan_alert(kerberos_alert())

    assert plan.feasible_hypotheses
    assert {item.hypothesis.hypothesis_id for item in plan.feasible_hypotheses} == {"H1", "H2"}
    assert {item.hypothesis.hypothesis_id for item in plan.rejected_hypotheses} == {"H3"}
    assert plan.actions[0].action_type == ActionType.ISOLATE_HOST
    assert plan.actions[0].score > plan.actions[-1].score


def test_executor_defaults_to_dry_run_and_records_audit() -> None:
    store = InMemoryKnowledgeStore()
    service = AgenticSOCService(knowledge_store=store)

    record = service.handle_alert(kerberos_alert())

    assert record.executed is True
    assert record.mode == "dry_run"
    assert len(record.results) == 3
    assert len(store.execution_records) == 1
    assert all(result.dry_run for result in record.results)


def test_live_execution_blocks_when_approval_is_required() -> None:
    settings = Settings(dry_run=False, auto_approval_max_business_impact=0.05)
    service = AgenticSOCService(settings=settings)

    record = service.handle_alert(kerberos_alert(), force_live=True)

    assert record.executed is False
    assert record.approval_state == ApprovalState.REQUIRES_ANALYST
    assert record.results[0].status == "blocked"


def test_api_plan_endpoint() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/incidents/plan",
        json={
            "source": "siem",
            "event_type": "Kerberos TGT Request",
            "source_user": "user123",
            "source_host": "ws-fin-27",
            "destination_host": "srv-fin-03",
            "result": "Success",
            "severity": "high",
            "attributes": {"process": "powershell.exe", "geo_velocity": "unusual"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["top_action"]["action_type"] == "ISOLATE_HOST"
    assert payload["feasible_hypotheses"]
