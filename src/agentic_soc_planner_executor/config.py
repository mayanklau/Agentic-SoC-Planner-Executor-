from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENTIC_SOC_", env_file=".env", extra="ignore")

    containment_weight: float = Field(default=0.7, ge=0, le=1)
    business_impact_weight: float = Field(default=0.25, ge=0, le=1)
    execution_cost_weight: float = Field(default=0.05, ge=0, le=1)
    auto_approval_max_business_impact: float = Field(default=0.25, ge=0, le=1)
    auto_approval_min_confidence: float = Field(default=0.55, ge=0, le=1)
    dry_run: bool = True
