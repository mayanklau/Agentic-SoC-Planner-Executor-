from agentic_soc_planner_executor.models import (
    ActionCandidate,
    ActionType,
    FeasibilityResult,
    Incident,
)


class AdaptivePlaybookGenerator:
    def candidates(
        self,
        incident: Incident,
        feasible_hypotheses: list[FeasibilityResult],
    ) -> list[ActionCandidate]:
        if not feasible_hypotheses:
            return [
                ActionCandidate(
                    action_type=ActionType.CREATE_TICKET,
                    target=incident.incident_id,
                    containment=0.10,
                    business_impact=0.0,
                    execution_cost=0.05,
                    rationale="No structurally feasible hypothesis survived validation.",
                    requires_approval=False,
                )
            ]

        source_host = incident.alert.source_host or "unknown-host"
        user = incident.alert.source_user or "unknown-user"
        criticality = incident.business_criticality
        high_confidence = max(item.hypothesis.confidence for item in feasible_hypotheses)

        return [
            ActionCandidate(
                action_type=ActionType.ISOLATE_HOST,
                target=source_host,
                containment=0.92,
                business_impact=min(0.15 + criticality * 0.10, 1.0),
                execution_cost=0.12,
                rationale=(
                    "Contain the suspected lateral movement source while preserving "
                    "identity access."
                ),
                requires_approval=criticality > 0.85,
                metadata={"max_hypothesis_confidence": high_confidence},
            ),
            ActionCandidate(
                action_type=ActionType.REVOKE_SESSION,
                target=user,
                containment=0.74,
                business_impact=0.18,
                execution_cost=0.08,
                rationale=(
                    "Revoke active sessions to interrupt credential misuse with "
                    "limited disruption."
                ),
                metadata={"max_hypothesis_confidence": high_confidence},
            ),
            ActionCandidate(
                action_type=ActionType.ENABLE_MFA,
                target=user,
                containment=0.62,
                business_impact=0.12,
                execution_cost=0.10,
                rationale=(
                    "Force stronger authentication because user MFA is absent or "
                    "bypass risk is high."
                ),
                metadata={"max_hypothesis_confidence": high_confidence},
            ),
            ActionCandidate(
                action_type=ActionType.MONITOR_ONLY,
                target=incident.incident_id,
                containment=0.15,
                business_impact=0.0,
                execution_cost=0.02,
                rationale="Passive monitoring retained as a low-disruption fallback.",
                metadata={"max_hypothesis_confidence": high_confidence},
            ),
        ]
