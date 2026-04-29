from agentic_soc_planner_executor.config import Settings
from agentic_soc_planner_executor.models import ActionCandidate


class RiskScoringEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def rank(self, actions: list[ActionCandidate]) -> list[ActionCandidate]:
        scored = []
        for action in actions:
            score = (
                self.settings.containment_weight * action.containment
                - self.settings.business_impact_weight * action.business_impact
                - self.settings.execution_cost_weight * action.execution_cost
            )
            scored.append(action.model_copy(update={"score": round(score, 4)}))
        return sorted(scored, key=lambda item: item.score, reverse=True)
