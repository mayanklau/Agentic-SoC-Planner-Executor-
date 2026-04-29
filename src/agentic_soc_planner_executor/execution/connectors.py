from typing import Protocol

from agentic_soc_planner_executor.models import ActionCandidate, ConnectorResult


class ActionConnector(Protocol):
    name: str

    def execute(self, action: ActionCandidate, dry_run: bool) -> ConnectorResult: ...


class AuditOnlyConnector:
    name = "audit-only"

    def execute(self, action: ActionCandidate, dry_run: bool) -> ConnectorResult:
        status = "simulated" if dry_run else "submitted"
        return ConnectorResult(
            action_type=action.action_type,
            target=action.target,
            status=status,
            dry_run=dry_run,
            message=f"{action.action_type} for {action.target} {status} via audit connector.",
            connector=self.name,
            metadata={"score": action.score, "rationale": action.rationale},
        )
