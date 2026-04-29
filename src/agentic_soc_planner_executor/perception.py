from agentic_soc_planner_executor.knowledge_store import KnowledgeStore
from agentic_soc_planner_executor.models import Incident, RawAlert


class PerceptionLayer:
    def __init__(self, knowledge_store: KnowledgeStore) -> None:
        self.knowledge_store = knowledge_store

    def enrich(self, alert: RawAlert) -> Incident:
        user = self.knowledge_store.get_identity(alert.source_user)
        source_asset = self.knowledge_store.get_asset(alert.source_host)
        target_asset = self.knowledge_store.get_asset(alert.destination_host)
        flags: set[str] = set()

        if alert.event_type.lower().startswith("kerberos"):
            flags.add("kerberos-authentication")
        if user and target_asset and user.business_unit != target_asset.business_unit:
            flags.add("cross-business-unit-access")
        if user and target_asset and user.privilege_tier > 1 and target_asset.criticality >= 0.8:
            flags.add("cross-tier-access")
        has_historical_access = self.knowledge_store.has_historical_access(
            alert.source_user,
            alert.destination_host,
        )
        if not has_historical_access:
            flags.add("no-prior-access")
        if alert.attributes.get("geo_velocity") == "unusual":
            flags.add("unusual-geo-velocity")
        if "powershell" in str(alert.attributes.get("process", "")).lower():
            flags.add("suspicious-powershell")

        return Incident(
            alert=alert,
            user=user,
            source_asset=source_asset,
            target_asset=target_asset,
            flags=flags,
            historical_baseline="known" if "no-prior-access" not in flags else "no prior access",
        )
