from agentic_soc_planner_executor.config import Settings
from agentic_soc_planner_executor.knowledge_store import KnowledgeStore
from agentic_soc_planner_executor.models import ApprovalState, Incident, ResponsePlan
from agentic_soc_planner_executor.planning.nce import (
    HeuristicCounterfactualEngine,
    HypothesisGenerator,
)
from agentic_soc_planner_executor.planning.playbooks import AdaptivePlaybookGenerator
from agentic_soc_planner_executor.planning.rsem import RiskScoringEngine
from agentic_soc_planner_executor.planning.sse import StructuralSimulationEngine


class Planner:
    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        settings: Settings | None = None,
        hypothesis_generator: HypothesisGenerator | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.hypothesis_generator = hypothesis_generator or HeuristicCounterfactualEngine()
        self.sse = StructuralSimulationEngine(knowledge_store)
        self.rsem = RiskScoringEngine(self.settings)
        self.playbooks = AdaptivePlaybookGenerator()

    def plan(self, incident: Incident) -> ResponsePlan:
        hypotheses = self.hypothesis_generator.generate(incident)
        feasibility = self.sse.validate(hypotheses)
        feasible = [item for item in feasibility if item.feasible]
        rejected = [item for item in feasibility if not item.feasible]
        actions = self.rsem.rank(self.playbooks.candidates(incident, feasible))
        approval_state = self._approval_state(feasible, actions)
        explanation = self._explain(feasible, rejected, actions, approval_state)
        return ResponsePlan(
            incident=incident,
            feasible_hypotheses=feasible,
            rejected_hypotheses=rejected,
            actions=actions,
            approval_state=approval_state,
            explanation=explanation,
        )

    def _approval_state(self, feasible: list, actions: list) -> ApprovalState:
        if not actions:
            return ApprovalState.REJECTED
        top_confidence = max((item.hypothesis.confidence for item in feasible), default=0.0)
        top_action = actions[0]
        if top_action.requires_approval:
            return ApprovalState.REQUIRES_ANALYST
        if top_confidence < self.settings.auto_approval_min_confidence:
            return ApprovalState.REQUIRES_ANALYST
        if top_action.business_impact > self.settings.auto_approval_max_business_impact:
            return ApprovalState.REQUIRES_ANALYST
        return ApprovalState.AUTO_APPROVED

    @staticmethod
    def _explain(
        feasible: list,
        rejected: list,
        actions: list,
        approval_state: ApprovalState,
    ) -> str:
        top_hypothesis = (
            feasible[0].hypothesis.description if feasible else "no feasible hypothesis"
        )
        top_action = actions[0].action_type if actions else "no action"
        return (
            f"Planner selected {top_action} because {top_hypothesis} survived structural "
            f"validation; {len(rejected)} hypothesis/hypotheses were rejected. "
            f"Approval state: {approval_state}."
        )
