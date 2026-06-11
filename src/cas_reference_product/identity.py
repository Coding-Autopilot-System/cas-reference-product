from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential


def build_credential(environment: str) -> TokenCredential:
    if environment == "local":
        return DefaultAzureCredential()
    return ManagedIdentityCredential()

