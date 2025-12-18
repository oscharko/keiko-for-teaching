"""Chat service components and protocols."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AIClientProtocol(Protocol):
    """Protocol defining the interface for AI chat clients.

    This protocol ensures consistent behavior across different AI backends
    (OpenAI, Azure OpenAI, Microsoft Foundry, etc.).
    """

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Generate a chat completion.

        Args:
            messages: List of chat messages with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters

        Returns:
            Chat completion response (format depends on implementation)
        """
        ...


__all__ = ["AIClientProtocol"]
