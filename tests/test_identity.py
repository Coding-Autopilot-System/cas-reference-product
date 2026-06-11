from unittest.mock import patch

from cas_reference_product.identity import build_credential


def test_local_uses_default_azure_credential() -> None:
    with patch("cas_reference_product.identity.DefaultAzureCredential") as credential:
        build_credential("local")
    credential.assert_called_once_with()


def test_azure_uses_system_assigned_managed_identity() -> None:
    with patch("cas_reference_product.identity.ManagedIdentityCredential") as credential:
        build_credential("prod")
    credential.assert_called_once_with()

