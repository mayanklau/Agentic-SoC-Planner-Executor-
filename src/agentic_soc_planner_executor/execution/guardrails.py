from agentic_soc_planner_executor.config import Settings
from agentic_soc_planner_executor.models import ApprovalState, ResponsePlan


class PolicyGuardrails:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def can_execute(self, plan: ResponsePlan) -> bool:
        if plan.approval_state != ApprovalState.AUTO_APPROVED:
            return False
        if not plan.top_action:
            return False
        return plan.top_action.business_impact <= self.settings.auto_approval_max_business_impact
