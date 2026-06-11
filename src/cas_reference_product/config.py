from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "cas-reference-product"
    environment: Literal["local", "dev", "test", "prod"] = "local"
    workflow_backend: Literal["local", "foundry"] = "local"
    repository: str = "Coding-Autopilot-System/cas-reference-product"
    foundry_project_endpoint: str | None = None
    foundry_agent_name: str | None = None
    applicationinsights_connection_string: str | None = Field(default=None, repr=False)

    @property
    def ready(self) -> bool:
        return self.workflow_backend == "local" or bool(
            self.foundry_project_endpoint and self.foundry_agent_name
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
