from agentic_soc_planner_executor.config import Settings
from agentic_soc_planner_executor.execution.connectors import ActionConnector, AuditOnlyConnector
from agentic_soc_planner_executor.execution.guardrails import PolicyGuardrails
from agentic_soc_planner_executor.knowledge_store import KnowledgeStore
from agentic_soc_planner_executor.models import (
    ActionType,
    ConnectorResult,
    ExecutionMode,
    ExecutionRecord,
    ResponsePlan,
)


class Executor:
    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        settings: Settings | None = None,
        connectors: dict[ActionType, ActionConnector] | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.knowledge_store = knowledge_store
        default_connector = AuditOnlyConnector()
        self.connectors = connectors or {
            action_type: default_connector for action_type in ActionType
        }
        self.guardrails = PolicyGuardrails(self.settings)

    def execute(self, plan: ResponsePlan, *, force_live: bool = False) -> ExecutionRecord:
        dry_run = self.settings.dry_run and not force_live
        execution_allowed = dry_run or self.guardrails.can_execute(plan)
        results: list[ConnectorResult] = []

        if not execution_allowed:
            results.append(
                ConnectorResult(
                    action_type=ActionType.CREATE_TICKET,
                    target=plan.incident.incident_id,
                    status="blocked",
                    dry_run=dry_run,
                    message="Policy guardrails require analyst approval before live execution.",
                    connector="policy-guardrails",
                )
            )
            record = self._record(plan, dry_run=dry_run, executed=False, results=results)
            self.knowledge_store.record_execution(record)
            return record

        for action in plan.actions[:3]:
            connector = self.connectors.get(action.action_type, AuditOnlyConnector())
            results.append(connector.execute(action, dry_run=dry_run))

        record = self._record(plan, dry_run=dry_run, executed=True, results=results)
        self.knowledge_store.record_execution(record)
        return record

    @staticmethod
    def _record(
        plan: ResponsePlan,
        *,
        dry_run: bool,
        executed: bool,
        results: list[ConnectorResult],
    ) -> ExecutionRecord:
        return ExecutionRecord(
            plan_id=plan.plan_id,
            incident_id=plan.incident.incident_id,
            mode=ExecutionMode.DRY_RUN if dry_run else ExecutionMode.LIVE,
            approval_state=plan.approval_state,
            executed=executed,
            results=results,
        )
