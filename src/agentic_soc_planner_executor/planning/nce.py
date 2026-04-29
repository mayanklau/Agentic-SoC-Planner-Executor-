from typing import Protocol

from agentic_soc_planner_executor.models import AttackHypothesis, Incident


class HypothesisGenerator(Protocol):
    def generate(self, incident: Incident) -> list[AttackHypothesis]: ...


class HeuristicCounterfactualEngine:
    """Deterministic NCE implementation suitable for CI and offline deployments."""

    def generate(self, incident: Incident) -> list[AttackHypothesis]:
        source = incident.alert.source_host or "unknown-source"
        target = incident.alert.destination_host or "unknown-target"
        flags = incident.flags

        misuse_confidence = 0.35
        if "no-prior-access" in flags:
            misuse_confidence += 0.16
        if "cross-tier-access" in flags:
            misuse_confidence += 0.16
        if "suspicious-powershell" in flags:
            misuse_confidence += 0.12
        if "unusual-geo-velocity" in flags:
            misuse_confidence += 0.08

        kerberos_confidence = 0.25
        if "kerberos-authentication" in flags:
            kerberos_confidence += 0.18
        if "cross-tier-access" in flags:
            kerberos_confidence += 0.10

        benign_confidence = 0.35
        if "no-prior-access" in flags:
            benign_confidence -= 0.08
        if "suspicious-powershell" in flags:
            benign_confidence -= 0.08
        if "unusual-geo-velocity" in flags:
            benign_confidence -= 0.05

        return [
            AttackHypothesis(
                hypothesis_id="H1",
                description="Credential misuse leading to lateral movement",
                confidence=min(misuse_confidence, 0.95),
                mitre_techniques=["T1078", "T1021"],
                required_edges=[(source, target)],
                required_conditions={"smb_allowed"},
                evidence=sorted(flags),
            ),
            AttackHypothesis(
                hypothesis_id="H2",
                description="Kerberos ticket abuse leading to privilege escalation",
                confidence=min(kerberos_confidence, 0.9),
                mitre_techniques=["T1558", "T1068"],
                required_edges=[(source, target)],
                required_conditions={"kerberos_enabled", "tier1_credentials_present"},
                evidence=sorted(flags),
            ),
            AttackHypothesis(
                hypothesis_id="H3",
                description="Benign service misconfiguration or approved administrative access",
                confidence=max(benign_confidence, 0.05),
                mitre_techniques=[],
                required_edges=[],
                required_conditions={"approved_change_window"},
                evidence=["benign counterfactual retained for comparison"],
            ),
        ]
