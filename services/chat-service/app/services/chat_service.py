"""Chat service for processing messages with Microsoft Foundry."""

import logging
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from openai import AsyncAzureOpenAI

from ..config import Settings
from .foundry_client import FoundryClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Du bist Keiko, ein hilfreicher KI-Assistent fuer Wissensmanagement.\n"
    "Antworte praezise und hilfreich auf Deutsch. Wenn du dir nicht sicher bist, "
    "sage es ehrlich."
)

RAG_SYSTEM_PROMPT = (
    "Du bist Keiko, ein hilfreicher KI-Assistent fuer Wissensmanagement.\n"
    "Nutze die folgenden Informationen aus der Wissensdatenbank, um die Frage zu "
    "beantworten.\n"
    "Wenn die Informationen nicht ausreichen, sage es ehrlich.\n"
    "Gib immer die Quellen an, die du verwendet hast."
)


class ChatService:
    """Service for handling chat interactions with Microsoft Foundry.

    Supports:
    - Multi-model inference (GPT-4o, Claude Sonnet 4.5, DeepSeek-V3)
    - Foundry IQ for agentic RAG (RAG 2.0)
    - Model Router for automatic model selection
    - Legacy Azure OpenAI for backward compatibility
    """

    def __init__(
        self,
        settings: Settings,
        http_client: httpx.AsyncClient | None = None,
        legacy_client: AsyncAzureOpenAI | None = None,
    ) -> None:
        """Initialize the chat service.

        Args:
            settings: Application settings
            http_client: HTTP client for calling other services
            legacy_client: Legacy Azure OpenAI client (for backward compatibility)
        """
        self._settings = settings
        self._http_client = http_client
        self._legacy_client = legacy_client

        # Initialize Foundry client if not using legacy mode
        if not settings.use_legacy_openai:
            self._foundry_client = FoundryClient(settings)
            logger.info("Chat service initialized with Microsoft Foundry")
        else:
            self._foundry_client = None
            logger.info("Chat service initialized with legacy Azure OpenAI")

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        suggest_followup: bool = True,
        use_rag: bool = False,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Process chat messages and return AI response.

        Args:
            messages: Chat message history
            temperature: Model temperature
            suggest_followup: Whether to generate follow-up questions
            use_rag: Whether to use RAG (Retrieval Augmented Generation)
            top_k: Number of documents to retrieve for RAG

        Returns:
            dict: Response with content, thoughts, citations, and follow-up questions
        """
        thoughts = []
        citations = []

        # Prepare chat messages
        if use_rag:
            # Use Foundry IQ for agentic RAG (RAG 2.0) if enabled
            if self._foundry_client and self._settings.enable_foundry_iq:
                thoughts.append({
                    "title": "Using Foundry IQ",
                    "description": "Agentic RAG with multi-source synthesis",
                })

                # Get the last user message as search query
                user_query = next(
                    (m["content"] for m in reversed(messages) if m["role"] == "user"),
                    "",
                )

                # Use Foundry IQ for intelligent knowledge grounding
                iq_result = await self._foundry_client.foundry_iq_search(
                    query=user_query,
                    knowledge_base="keiko-documents",
                    retrieval_effort=self._settings.foundry_iq_retrieval_effort,
                )

                content = iq_result["answer"]
                citations = iq_result["citations"]
                thoughts.append({
                    "title": "Foundry IQ completed",
                    "description": f"Retrieved {len(citations)} sources with agentic "
                                   "reasoning",
                })

                # Return Foundry IQ result
                result: dict[str, Any] = {
                    "content": content,
                    "thoughts": thoughts,
                    "citations": citations,
                }

                if suggest_followup:
                    result["followup_questions"] = (
                        await self._generate_followup_questions(messages, content)
                    )

                return result

            # Fallback to traditional RAG if Foundry IQ not enabled
            elif self._http_client:
                thoughts.append({
                    "title": "Searching knowledge base",
                    "description": ""
                })

                # Get the last user message as search query
                user_query = next(
                    (m["content"] for m in reversed(messages) if m["role"] == "user"),
                    "",
                )

                # Call search service
                search_results = await self._search_documents(user_query, top_k)

                if search_results:
                    thoughts.append({
                        "title": "Retrieved documents",
                        "description": f"Found {len(search_results)} documents",
                    })

                    # Build context from search results
                    context = self._build_rag_context(search_results)
                    citations = [doc.get("id", "") for doc in search_results]

                    # Use RAG system prompt with context
                    chat_messages = [
                        {"role": "system", "content": RAG_SYSTEM_PROMPT},
                        {"role": "system", "content": f"Kontext:\n{context}"},
                    ]
                else:
                    thoughts.append({
                        "title": "No documents found",
                        "description": "Falling back to general knowledge",
                    })
                    chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            else:
                chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        else:
            # Standard chat without RAG
            chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        chat_messages.extend(messages)

        # Generate response using Foundry or legacy OpenAI
        if self._foundry_client:
            # Use Microsoft Foundry
            response = await self._foundry_client.chat_completion(
                messages=chat_messages,
                temperature=temperature,
                max_tokens=self._settings.default_max_tokens,
                use_model_router=self._settings.enable_model_router,
            )
            content = response.choices[0].message.content or ""
        else:
            # Use legacy Azure OpenAI
            response = await self._legacy_client.chat.completions.create(
                model=self._settings.azure_openai_deployment,
                messages=chat_messages,  # type: ignore[arg-type]
                temperature=temperature or self._settings.default_temperature,
                max_tokens=self._settings.default_max_tokens,
            )
            content = response.choices[0].message.content or ""
        result: dict[str, Any] = {
            "content": content,
            "thoughts": thoughts,
            "citations": citations,
        }

        if suggest_followup:
            result["followup_questions"] = await self._generate_followup_questions(
                messages, content
            )

        return result

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        use_rag: bool = False,
        top_k: int = 5,
    ) -> AsyncGenerator[str, None]:
        """Process chat messages and stream AI response.

        Args:
            messages: Chat message history
            temperature: Model temperature
            use_rag: Whether to use RAG
            top_k: Number of documents to retrieve for RAG

        Yields:
            str: Response chunks
        """
        # Prepare chat messages (same as non-streaming)
        if use_rag and self._http_client:
            user_query = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"),
                "",
            )
            search_results = await self._search_documents(user_query, top_k)

            if search_results:
                context = self._build_rag_context(search_results)
                chat_messages = [
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {"role": "system", "content": f"Kontext:\n{context}"},
                ]
            else:
                chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        else:
            chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        chat_messages.extend(messages)

        # Stream response using appropriate client
        if self._foundry_client:
            # Foundry streaming not yet implemented - fall back to non-streaming
            logger.warning("Streaming not yet supported with Foundry, using legacy")

        if not self._legacy_client:
            raise RuntimeError("No AI client available for streaming")

        stream = await self._legacy_client.chat.completions.create(
            model=self._settings.azure_openai_deployment,
            messages=chat_messages,  # type: ignore[arg-type]
            temperature=temperature or self._settings.default_temperature,
            max_tokens=self._settings.default_max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _search_documents(
        self, query: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Search for relevant documents using the search service.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            list: Search results
        """
        if not self._http_client:
            logger.warning("HTTP client not available for RAG search")
            return []

        try:
            response = await self._http_client.post(
                f"{self._settings.search_service_url}/api/search",
                json={
                    "query": query,
                    "top_k": top_k,
                    "use_semantic_ranker": True,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("results", [])

        except Exception as e:
            logger.error(f"Search service error: {e}")
            return []

    def _build_rag_context(self, search_results: list[dict[str, Any]]) -> str:
        """Build context string from search results.

        Args:
            search_results: List of search results

        Returns:
            str: Formatted context string
        """
        context_parts = []
        for i, doc in enumerate(search_results, 1):
            content = doc.get("content", "")
            source = doc.get("id", f"Document {i}")
            context_parts.append(f"[{i}] Quelle: {source}\n{content}")

        return "\n\n".join(context_parts)

    async def _generate_followup_questions(
        self, messages: list[dict[str, str]], response: str
    ) -> list[str]:
        """Generate follow-up questions based on the conversation.

        Args:
            messages: Chat message history
            response: AI response

        Returns:
            list: Follow-up questions
        """
        prompt = (
            "Based on this conversation, generate 3 short follow-up questions.\n"
            f"Response: {response}\n"
            "Return only the questions, one per line, without numbering."
        )

        followup_messages = [{"role": "user", "content": prompt}]

        # Use Foundry client if available, otherwise legacy client
        if self._foundry_client:
            followup_response = await self._foundry_client.chat_completion(
                messages=followup_messages,
                temperature=0.7,
                max_tokens=200,
            )
            content = followup_response.choices[0].message.content or ""
        elif self._legacy_client:
            followup_response = await self._legacy_client.chat.completions.create(
                model=self._settings.azure_openai_deployment,
                messages=followup_messages,  # type: ignore[arg-type]
                temperature=0.7,
                max_tokens=200,
            )
            content = followup_response.choices[0].message.content or ""
        else:
            logger.warning("No AI client available for follow-up questions")
            return []

        return [q.strip() for q in content.strip().split("\n") if q.strip()][:3]

