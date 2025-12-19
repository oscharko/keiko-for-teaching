"""Microsoft Foundry client for multi-model AI inference and agent orchestration."""

import logging
from typing import Any

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    ChatCompletions,
    ChatRequestMessage,
    SystemMessage,
    UserMessage,
)
from azure.ai.projects import AIProjectClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from ..config import Settings

logger = logging.getLogger(__name__)


class FoundryClient:
    """Client for Microsoft Foundry AI services.

    This client provides access to:
    - Multi-model inference (GPT-4o, Claude Sonnet 4.5, DeepSeek-V3, etc.)
    - Foundry Agent Service (hosted agents with tool orchestration)
    - Foundry IQ (agentic RAG with multi-source synthesis)
    - Model Router (automatic model selection based on query complexity)
    """

    def __init__(self, settings: Settings):
        """Initialize Foundry client.

        Args:
            settings: Application settings with Foundry configuration
        """
        self._settings = settings

        # Initialize credential
        if settings.foundry_api_key:
            # Local development with API key
            self._credential = AzureKeyCredential(settings.foundry_api_key)
        else:
            # Production with Managed Identity
            self._credential = DefaultAzureCredential(
                managed_identity_client_id=settings.azure_client_id
            )

        # Initialize AI Project Client (for Foundry Agent Service)
        self._project_client = AIProjectClient(
            endpoint=settings.foundry_endpoint,
            credential=self._credential,
            subscription_id=settings.azure_subscription_id,
            resource_group_name=settings.azure_resource_group,
            project_name=settings.foundry_project_name,
        )

        # Initialize Chat Completions Client (for multi-model inference)
        self._chat_client = ChatCompletionsClient(
            endpoint=f"{settings.foundry_endpoint}/models",
            credential=self._credential,
        )

        logger.info(
            f"Foundry client initialized - Project: {settings.foundry_project_name}, "
            f"Default Model: {settings.foundry_default_model}"
        )

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        use_model_router: bool = False,
    ) -> ChatCompletions:
        """Generate chat completion using Foundry models.

        Args:
            messages: Chat message history
            model: Model to use (gpt-4o, claude-sonnet-4.5, deepseek-v3, etc.)
                   If None, uses default model from settings
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            use_model_router: Use Foundry Model Router for automatic model selection

        Returns:
            ChatCompletions: Response from the model
        """
        # Convert messages to Foundry format
        foundry_messages: list[ChatRequestMessage] = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                foundry_messages.append(SystemMessage(content=content))
            elif role == "user":
                foundry_messages.append(UserMessage(content=content))
            elif role == "assistant":
                foundry_messages.append(AssistantMessage(content=content))

        # Determine model to use
        target_model = model or self._settings.foundry_default_model

        # Use Model Router if enabled
        if use_model_router:
            target_model = "model-router"  # Foundry's automatic model selection
            logger.info("Using Foundry Model Router for automatic model selection")

        logger.info(f"Generating completion with model: {target_model}")

        # Generate completion
        response = await self._chat_client.complete(
            model=target_model,
            messages=foundry_messages,
            temperature=temperature or self._settings.default_temperature,
            max_tokens=max_tokens or self._settings.default_max_tokens,
        )

        return response

    async def create_agent(
        self,
        name: str,
        instructions: str,
        model: str | None = None,
        tools: list[str] | None = None,
    ) -> Any:
        """Create a Foundry Agent.

        Args:
            name: Agent name
            instructions: System instructions for the agent
            model: Model to use for the agent
            tools: List of tools to enable (file_search, code_interpreter, etc.)

        Returns:
            Agent: Created agent instance
        """
        agent = await self._project_client.agents.create_agent(
            model=model or self._settings.foundry_default_model,
            name=name,
            instructions=instructions,
            tools=tools or [],
        )

        logger.info(f"Created Foundry Agent: {name} (ID: {agent.id})")
        return agent

    async def create_thread(self) -> Any:
        """Create a conversation thread for agent interactions.

        Returns:
            AgentThread: Created thread instance
        """
        thread = await self._project_client.agents.create_thread()
        logger.info(f"Created agent thread: {thread.id}")
        return thread

    async def send_message(
        self,
        thread_id: str,
        content: str,
        agent_id: str,
    ) -> list[Any]:
        """Send a message to an agent thread and get response.

        Args:
            thread_id: Thread ID
            content: Message content
            agent_id: Agent ID to process the message

        Returns:
            list[ThreadMessage]: Agent's response messages
        """
        # Add user message to thread
        await self._project_client.agents.create_message(
            thread_id=thread_id,
            role="user",
            content=content,
        )

        # Run the agent
        run = await self._project_client.agents.create_run(
            thread_id=thread_id,
            agent_id=agent_id,
        )

        # Wait for completion
        while run.status in ["queued", "in_progress"]:
            run = await self._project_client.agents.get_run(
                thread_id=thread_id,
                run_id=run.id,
            )

        # Get messages
        messages = await self._project_client.agents.list_messages(
            thread_id=thread_id,
        )

        return messages.data

    async def foundry_iq_search(
        self,
        query: str,
        knowledge_base: str,
        retrieval_effort: str = "medium",
    ) -> dict[str, Any]:
        """Search using Foundry IQ (agentic RAG).

        Foundry IQ provides intelligent knowledge grounding with:
        - Agentic reasoning for query understanding
        - Multi-source synthesis
        - Enterprise permission enforcement
        - Automatic citation generation

        Args:
            query: Search query
            knowledge_base: Knowledge base name
            retrieval_effort: Effort level (low, medium, high)
                             Higher effort = more agentic reasoning

        Returns:
            dict: Search results with synthesized answer and citations
        """
        # Foundry IQ uses the AI Project's knowledge base
        # This is a simplified implementation - actual Foundry IQ API may differ
        logger.info(
            f"Foundry IQ search - Query: {query}, KB: {knowledge_base}, "
            f"Effort: {retrieval_effort}"
        )

        # Use agent with file_search tool for Foundry IQ
        agent = await self.create_agent(
            name="foundry-iq-agent",
            instructions=(
                "You are a knowledge retrieval agent. "
                "Search the knowledge base and synthesize information from multiple "
                "sources. Always provide citations for your answers."
            ),
            tools=["file_search"],
        )

        thread = await self.create_thread()
        messages = await self.send_message(
            thread_id=thread.id,
            content=query,
            agent_id=agent.id,
        )

        # Extract answer and citations
        answer = messages[0].content if messages else ""
        citations = self._extract_citations(messages)

        return {
            "answer": answer,
            "citations": citations,
            "knowledge_base": knowledge_base,
            "retrieval_effort": retrieval_effort,
        }

    def _extract_citations(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Extract citations from agent messages.

        Args:
            messages: Agent messages

        Returns:
            list: Extracted citations
        """
        citations = []
        for message in messages:
            if hasattr(message, "annotations"):
                for annotation in message.annotations:
                    if hasattr(annotation, "file_citation"):
                        citations.append({
                            "file_id": annotation.file_citation.file_id,
                            "quote": annotation.file_citation.quote,
                        })
        return citations

    async def close(self):
        """Close the Foundry client and cleanup resources."""
        # Close clients if they have close methods
        if hasattr(self._chat_client, "close"):
            await self._chat_client.close()
        if hasattr(self._project_client, "close"):
            await self._project_client.close()

        logger.info("Foundry client closed")

