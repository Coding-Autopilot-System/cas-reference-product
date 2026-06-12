from unittest.mock import patch

import pytest

from cas_reference_product.config import Settings
from cas_reference_product.workflow import (
    FoundryWorkflowAgentService,
    LocalWorkflowAgentService,
    WorkflowAgentServiceError,
    build_workflow_agent_service,
)


def test_factory_builds_local_service() -> None:
    assert isinstance(build_workflow_agent_service(Settings()), LocalWorkflowAgentService)


def test_factory_builds_foundry_service_when_configured() -> None:
    settings = Settings(
        environment="prod",
        workflow_backend="foundry",
        foundry_project_endpoint="https://example.services.ai.azure.com/api/projects/example",
        foundry_agent_name="cas-reference-agent",
    )
    with patch("cas_reference_product.workflow.FoundryWorkflowAgentService") as service:
        build_workflow_agent_service(settings)
    service.assert_called_once_with(settings)


def test_foundry_service_uses_next_gen_agent_reference(envelope) -> None:
    settings = Settings(
        environment="prod",
        workflow_backend="foundry",
        foundry_project_endpoint="https://example.services.ai.azure.com/api/projects/example",
        foundry_agent_name="cas-reference-agent",
    )
    with (
        patch("cas_reference_product.workflow.build_credential") as credential,
        patch("cas_reference_product.workflow.AIProjectClient") as project_client,
    ):
        responses = project_client.return_value.get_openai_client.return_value.responses
        responses.create.return_value.output_text = "Foundry result"
        service = FoundryWorkflowAgentService(settings)
        result = service.run(envelope)

    project_client.assert_called_once_with(
        endpoint=settings.foundry_project_endpoint,
        credential=credential.return_value,
    )
    responses.create.assert_called_once_with(
        input=envelope.prompt,
        extra_body={
            "agent_reference": {
                "name": "cas-reference-agent",
                "type": "agent_reference",
            }
        },
    )
    assert result == "Foundry result"


def test_foundry_service_sanitizes_sdk_failure(envelope) -> None:
    settings = Settings(
        environment="prod",
        workflow_backend="foundry",
        foundry_project_endpoint="https://example.services.ai.azure.com/api/projects/example",
        foundry_agent_name="cas-reference-agent",
    )
    with (
        patch("cas_reference_product.workflow.build_credential"),
        patch("cas_reference_product.workflow.AIProjectClient") as project_client,
    ):
        project_client.return_value.get_openai_client.return_value.responses.create.side_effect = (
            RuntimeError("sensitive provider detail")
        )
        service = FoundryWorkflowAgentService(settings)

        with pytest.raises(WorkflowAgentServiceError, match="Foundry workflow invocation failed"):
            service.run(envelope)
