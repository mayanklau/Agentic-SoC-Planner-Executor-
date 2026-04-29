# Architecture Notes

This component packages the paper's AgentSOC ideas as a backend-ready planner/executor service.

## Design Decisions

1. Planner and executor are separate trust boundaries.
   The planner creates a `ResponsePlan` with hypotheses, feasibility decisions, action scores, and explanations. It does not call production systems.

2. The executor is policy gated.
   The executor receives a plan, evaluates guardrails, and dispatches connector calls only when the plan is auto-approved or when running in dry-run mode.

3. NCE is swappable.
   `HypothesisGenerator` is a protocol. The default implementation is deterministic for tests and offline operation, while production can inject an LLM-backed NCE.

4. SSE grounds reasoning in enterprise structure.
   `StructuralSimulationEngine` validates required graph edges and environmental conditions before a hypothesis is allowed to influence action selection.

5. RSEM quantifies action tradeoffs.
   `RiskScoringEngine` ranks containment actions using tunable weights for containment value, business impact, and execution cost.

6. Connectors are isolated from planning.
   SOAR, EDR, IAM, ticketing, and notification integrations should implement `ActionConnector` and be registered by `ActionType`.

## Integration Pattern

```python
from agentic_soc_planner_executor import AgenticSOCService
from agentic_soc_planner_executor.models import RawAlert

service = AgenticSOCService(
    knowledge_store=my_enterprise_store,
    executor=my_connector_backed_executor,
)

plan = service.plan_alert(RawAlert.model_validate(payload))
record = service.handle_alert(RawAlert.model_validate(payload))
```

Use `plan_alert` for analyst review, approvals, and explainability workflows. Use `handle_alert` for closed-loop automation under guardrails.

## Production Extension Points

- Replace `InMemoryKnowledgeStore` with CMDB, IAM, topology, GRC, and MITRE ATT&CK backed adapters.
- Inject an LLM-backed `HypothesisGenerator` that emits `AttackHypothesis` objects with evidence and required structural conditions.
- Register live `ActionConnector` implementations for SOAR, EDR, IAM, and ticketing tools.
- Persist `ExecutionRecord` objects to the SOC audit log or case-management system.
- Feed execution outcomes back into the knowledge store for future scoring and analyst trust calibration.
