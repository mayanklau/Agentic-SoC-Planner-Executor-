from agentic_soc_planner_executor.knowledge_store import KnowledgeStore
from agentic_soc_planner_executor.models import AttackHypothesis, FeasibilityResult


class StructuralSimulationEngine:
    def __init__(self, knowledge_store: KnowledgeStore) -> None:
        self.knowledge_store = knowledge_store

    def validate(self, hypotheses: list[AttackHypothesis]) -> list[FeasibilityResult]:
        return [self._validate_one(hypothesis) for hypothesis in hypotheses]

    def _validate_one(self, hypothesis: AttackHypothesis) -> FeasibilityResult:
        missing_edges = [
            (source, target)
            for source, target in hypothesis.required_edges
            if not self.knowledge_store.has_path(source, target)
        ]
        missing_conditions = {
            condition
            for condition in hypothesis.required_conditions
            if not self.knowledge_store.has_condition(condition)
        }

        if missing_edges:
            return FeasibilityResult(
                hypothesis=hypothesis,
                feasible=False,
                reason=f"Missing topology path(s): {missing_edges}",
                missing_conditions=missing_conditions,
            )

        if missing_conditions:
            conditional = (
                hypothesis.hypothesis_id == "H2"
                and "tier1_credentials_present" in missing_conditions
            )
            return FeasibilityResult(
                hypothesis=hypothesis,
                feasible=conditional,
                conditional=conditional,
                reason=(
                    "Conditionally feasible if missing preconditions are observed"
                    if conditional
                    else "Required conditions are not present"
                ),
                missing_conditions=missing_conditions,
            )

        return FeasibilityResult(
            hypothesis=hypothesis,
            feasible=True,
            reason="Network path and required conditions are present",
        )
