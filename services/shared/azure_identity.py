"""Azure Identity credential factory with environment detection.

This module provides a unified way to obtain Azure credentials across different
environments (local development, Azure Kubernetes Service, etc.).
"""

import os

from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    DefaultAzureCredential,
    EnvironmentCredential,
    ManagedIdentityCredential,
)
from azure.core.credentials import TokenCredential


def get_azure_credential(
    managed_identity_client_id: str | None = None,
) -> TokenCredential:
    """Get Azure credential based on the current environment.

    This function implements a credential chain that tries different authentication
    methods in order:
    1. Environment variables (for local development with service principal)
    2. Managed Identity (for Azure Kubernetes Service)
    3. Azure CLI (for local development)
    4. Default Azure Credential (fallback)

    Args:
        managed_identity_client_id: Optional client ID for user-assigned managed identity.
            If not provided, will use AZURE_CLIENT_ID environment variable.

    Returns:
        TokenCredential: An Azure credential object that can be used with Azure SDKs.

    Example:
        >>> credential = get_azure_credential()
        >>> # Use with Azure OpenAI
        >>> from openai import AzureOpenAI
        >>> client = AzureOpenAI(
        ...     azure_endpoint="https://your-endpoint.openai.azure.com",
        ...     azure_ad_token_provider=get_bearer_token_provider(
        ...         credential, "https://cognitiveservices.azure.com/.default"
        ...     ),
        ...     api_version="2024-08-01-preview",
        ... )
    """
    # Detect environment
    is_kubernetes = os.getenv("KUBERNETES_SERVICE_HOST") is not None
    has_env_credentials = all(
        [
            os.getenv("AZURE_TENANT_ID"),
            os.getenv("AZURE_CLIENT_ID"),
            os.getenv("AZURE_CLIENT_SECRET"),
        ]
    )

    # Get managed identity client ID
    client_id = managed_identity_client_id or os.getenv("AZURE_CLIENT_ID")

    credentials = []

    # 1. Try environment credentials first (for local dev with service principal)
    if has_env_credentials:
        credentials.append(EnvironmentCredential())

    # 2. Try managed identity (for AKS)
    if is_kubernetes or client_id:
        if client_id:
            # User-assigned managed identity
            credentials.append(ManagedIdentityCredential(client_id=client_id))
        else:
            # System-assigned managed identity
            credentials.append(ManagedIdentityCredential())

    # 3. Try Azure CLI (for local development)
    if not is_kubernetes:
        credentials.append(AzureCliCredential())

    # 4. Fallback to DefaultAzureCredential
    if not credentials:
        return DefaultAzureCredential()

    # Return chained credential
    return ChainedTokenCredential(*credentials)


def is_local_development() -> bool:
    """Check if running in local development environment.

    Returns:
        bool: True if running locally, False if running in Azure (AKS).
    """
    return os.getenv("KUBERNETES_SERVICE_HOST") is None


def is_managed_identity_available() -> bool:
    """Check if managed identity is available in the current environment.

    Returns:
        bool: True if managed identity is available, False otherwise.
    """
    # Check if running in Kubernetes
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return True

    # Check if managed identity client ID is configured
    if os.getenv("AZURE_CLIENT_ID"):
        return True

    return False


def get_credential_info() -> dict[str, str]:
    """Get information about the credential configuration.

    Returns:
        dict: Dictionary containing credential configuration information.
    """
    return {
        "environment": "local" if is_local_development() else "azure",
        "managed_identity_available": str(is_managed_identity_available()),
        "has_env_credentials": str(
            all(
                [
                    os.getenv("AZURE_TENANT_ID"),
                    os.getenv("AZURE_CLIENT_ID"),
                    os.getenv("AZURE_CLIENT_SECRET"),
                ]
            )
        ),
        "has_cli_credentials": str(
            os.system("az account show > /dev/null 2>&1") == 0
        ),
    }

