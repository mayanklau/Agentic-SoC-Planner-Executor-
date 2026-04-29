from __future__ import annotations

from collections import deque
from typing import Protocol

from agentic_soc_planner_executor.models import AssetProfile, ExecutionRecord, IdentityProfile


class KnowledgeStore(Protocol):
    def get_identity(self, user: str | None) -> IdentityProfile | None: ...
    def get_asset(self, host: str | None) -> AssetProfile | None: ...
    def has_path(self, source: str | None, target: str | None) -> bool: ...
    def has_historical_access(self, user: str | None, target: str | None) -> bool: ...
    def has_condition(self, condition: str) -> bool: ...
    def record_execution(self, record: ExecutionRecord) -> None: ...


class InMemoryKnowledgeStore:
    def __init__(self) -> None:
        self.identities: dict[str, IdentityProfile] = {
            "user123": IdentityProfile(
                user="user123",
                privilege_tier=2,
                business_unit="finance",
                mfa_enabled=False,
                groups={"finance-users", "smb-access"},
            )
        }
        self.assets: dict[str, AssetProfile] = {
            "ws-fin-27": AssetProfile(
                host="ws-fin-27",
                business_unit="finance",
                criticality=0.35,
                tags={"workstation"},
            ),
            "srv-fin-03": AssetProfile(
                host="srv-fin-03",
                business_unit="finance",
                criticality=0.90,
                tags={"database", "critical"},
            ),
        }
        self.reachability: dict[str, set[str]] = {
            "ws-fin-27": {"srv-fin-03"},
            "srv-fin-03": set(),
        }
        self.historical_access: set[tuple[str, str]] = set()
        self.conditions: set[str] = {"smb_allowed", "kerberos_enabled"}
        self.execution_records: list[ExecutionRecord] = []

    def get_identity(self, user: str | None) -> IdentityProfile | None:
        if user is None:
            return None
        return self.identities.get(user)

    def get_asset(self, host: str | None) -> AssetProfile | None:
        if host is None:
            return None
        return self.assets.get(host)

    def has_path(self, source: str | None, target: str | None) -> bool:
        if source is None or target is None:
            return False
        if source == target:
            return True
        seen = {source}
        queue: deque[str] = deque([source])
        while queue:
            current = queue.popleft()
            for neighbor in self.reachability.get(current, set()):
                if neighbor == target:
                    return True
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        return False

    def has_historical_access(self, user: str | None, target: str | None) -> bool:
        return user is not None and target is not None and (user, target) in self.historical_access

    def has_condition(self, condition: str) -> bool:
        return condition in self.conditions

    def record_execution(self, record: ExecutionRecord) -> None:
        self.execution_records.append(record)
