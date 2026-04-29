# Agentic SOC Planner Executor

Production-grade planner/executor backend component for an Agentic SOC platform. It implements the paper’s core pattern:

- Perception layer normalizes and enriches alerts into incident objects.
- Planner generates counterfactual attack hypotheses, validates them against enterprise structure, and ranks response actions.
- Executor enforces policy guardrails, defaults to dry-run, emits auditable execution records, and feeds outcomes back into the knowledge store.

The design keeps planning and execution explicitly separated so the backend can recommend, approve, simulate, and execute through different trust boundaries.

## Architecture

```text
Alert -> Perception -> Planner
                    -> NCE: hypothesis generation
                    -> SSE: graph feasibility validation
                    -> RSEM: risk-aware action ranking
                    -> ResponsePlan

ResponsePlan -> PolicyGuardrails -> Executor connectors -> ExecutionRecord -> KnowledgeStore feedback
```

## Quick Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn agentic_soc_planner_executor.api:create_app --factory --reload
```

Submit an alert:

```bash
curl -X POST http://127.0.0.1:8000/incidents/execute \
  -H 'content-type: application/json' \
  -d @examples/kerberos_alert.json
```

## Product Interfaces

- `Planner.plan(incident)` returns a response plan without side effects.
- `Executor.execute(plan)` applies policy gates and dispatches dry-run or live connector actions.
- `AgenticSOCService.handle_alert(alert, execute=True)` runs the end-to-end sense-reason-act cycle.
- `create_app()` exposes `/incidents/plan`, `/incidents/execute`, and `/health`.

## Production Defaults

- Dry-run execution is enabled by default.
- High-impact or low-confidence plans require analyst approval.
- Every decision and connector attempt is captured in an execution record.
- The default hypothesis generator is deterministic for testing; an LLM implementation can be injected behind the `HypothesisGenerator` protocol.
- Action dispatch uses connector interfaces so SOAR, EDR, IAM, and ticketing integrations can be added without changing planner logic.
