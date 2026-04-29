from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionMode(StrEnum):
    DRY_RUN = "dry_run"
    LIVE = "live"


class ApprovalState(StrEnum):
    AUTO_APPROVED = "auto_approved"
    REQUIRES_ANALYST = "requires_analyst"
    REJECTED = "rejected"


class ActionType(StrEnum):
    ISOLATE_HOST = "ISOLATE_HOST"
    DISABLE_USER = "DISABLE_USER"
    REVOKE_SESSION = "REVOKE_SESSION"
    RESTRICT_PRIVILEGES = "RESTRICT_PRIVILEGES"
    ENABLE_MFA = "ENABLE_MFA"
    QUARANTINE_ACCESS = "QUARANTINE_ACCESS"
    MONITOR_ONLY = "MONITOR_ONLY"
    CREATE_TICKET = "CREATE_TICKET"


class RawAlert(BaseModel):
    source: str
    event_type: str
    source_user: str | None = None
    source_host: str | None = None
    destination_host: str | None = None
    result: str | None = None
    severity: Severity = Severity.MEDIUM
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    attributes: dict[str, Any] = Field(default_factory=dict)


class AssetProfile(BaseModel):
    host: str
    business_unit: str = "unknown"
    criticality: float = Field(default=0.5, ge=0, le=1)
    tags: set[str] = Field(default_factory=set)


class IdentityProfile(BaseModel):
    user: str
    privilege_tier: int = Field(default=3, ge=0, le=5)
    business_unit: str = "unknown"
    mfa_enabled: bool = True
    groups: set[str] = Field(default_factory=set)


class Incident(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"INC-{uuid4().hex[:12].upper()}")
    alert: RawAlert
    user: IdentityProfile | None = None
    source_asset: AssetProfile | None = None
    target_asset: AssetProfile | None = None
    flags: set[str] = Field(default_factory=set)
    historical_baseline: str = "unknown"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field
    @property
    def business_criticality(self) -> float:
        values = [
            asset.criticality
            for asset in (self.source_asset, self.target_asset)
            if asset is not None
        ]
        return max(values, default=0.0)


class AttackHypothesis(BaseModel):
    hypothesis_id: str
    description: str
    confidence: float = Field(ge=0, le=1)
    mitre_techniques: list[str] = Field(default_factory=list)
    required_edges: list[tuple[str, str]] = Field(default_factory=list)
    required_conditions: set[str] = Field(default_factory=set)
    evidence: list[str] = Field(default_factory=list)


class FeasibilityResult(BaseModel):
    hypothesis: AttackHypothesis
    feasible: bool
    conditional: bool = False
    reason: str
    missing_conditions: set[str] = Field(default_factory=set)


class ActionCandidate(BaseModel):
    action_type: ActionType
    target: str
    containment: float = Field(ge=0, le=1)
    business_impact: float = Field(ge=0, le=1)
    execution_cost: float = Field(default=0.0, ge=0, le=1)
    rationale: str
    requires_approval: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0


class ResponsePlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"PLAN-{uuid4().hex[:12].upper()}")
    incident: Incident
    feasible_hypotheses: list[FeasibilityResult]
    rejected_hypotheses: list[FeasibilityResult]
    actions: list[ActionCandidate]
    approval_state: ApprovalState
    explanation: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field
    @property
    def top_action(self) -> ActionCandidate | None:
        return self.actions[0] if self.actions else None


class ConnectorResult(BaseModel):
    action_type: ActionType
    target: str
    status: str
    dry_run: bool
    message: str
    connector: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionRecord(BaseModel):
    execution_id: str = Field(default_factory=lambda: f"EXE-{uuid4().hex[:12].upper()}")
    plan_id: str
    incident_id: str
    mode: ExecutionMode
    approval_state: ApprovalState
    executed: bool
    results: list[ConnectorResult]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
