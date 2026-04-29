from agentic_soc_planner_executor.config import Settings
from agentic_soc_planner_executor.models import ActionCandidate, ActionType
from agentic_soc_planner_executor.planning.rsem import RiskScoringEngine


def test_rsem_balances_containment_impact_and_cost() -> None:
    engine = RiskScoringEngine(
        Settings(containment_weight=0.7, business_impact_weight=0.25, execution_cost_weight=0.05)
    )
    actions = [
        ActionCandidate(
            action_type=ActionType.DISABLE_USER,
            target="user123",
            containment=0.9,
            business_impact=0.8,
            execution_cost=0.1,
            rationale="Strong but disruptive.",
        ),
        ActionCandidate(
            action_type=ActionType.REVOKE_SESSION,
            target="user123",
            containment=0.75,
            business_impact=0.15,
            execution_cost=0.05,
            rationale="Balanced response.",
        ),
    ]

    ranked = engine.rank(actions)

    assert ranked[0].action_type == ActionType.REVOKE_SESSION
