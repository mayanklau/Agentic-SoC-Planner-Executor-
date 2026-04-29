from agentic_soc_planner_executor.config import Settings
from agentic_soc_planner_executor.executor import Executor
from agentic_soc_planner_executor.knowledge_store import InMemoryKnowledgeStore, KnowledgeStore
from agentic_soc_planner_executor.models import ExecutionRecord, RawAlert, ResponsePlan
from agentic_soc_planner_executor.perception import PerceptionLayer
from agentic_soc_planner_executor.planner import Planner


class AgenticSOCService:
    def __init__(
        self,
        knowledge_store: KnowledgeStore | None = None,
        settings: Settings | None = None,
        planner: Planner | None = None,
        executor: Executor | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.knowledge_store = knowledge_store or InMemoryKnowledgeStore()
        self.perception = PerceptionLayer(self.knowledge_store)
        self.planner = planner or Planner(self.knowledge_store, self.settings)
        self.executor = executor or Executor(self.knowledge_store, self.settings)

    def plan_alert(self, alert: RawAlert) -> ResponsePlan:
        incident = self.perception.enrich(alert)
        return self.planner.plan(incident)

    def handle_alert(self, alert: RawAlert, *, force_live: bool = False) -> ExecutionRecord:
        plan = self.plan_alert(alert)
        return self.executor.execute(plan, force_live=force_live)
