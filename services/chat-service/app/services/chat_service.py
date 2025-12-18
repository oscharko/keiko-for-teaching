"""Chat service for processing messages with Azure OpenAI."""

import logging
from typing import Any, AsyncGenerator

import httpx
from openai import AsyncAzureOpenAI

from ..config import Settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du bist Keiko, ein hilfreicher KI-Assistent fuer Wissensmanagement.
Antworte praezise und hilfreich auf Deutsch. Wenn du dir nicht sicher bist, sage es ehrlich."""

RAG_SYSTEM_PROMPT = """Du bist Keiko, ein hilfreicher KI-Assistent fuer Wissensmanagement.
Nutze die folgenden Informationen aus der Wissensdatenbank, um die Frage zu beantworten.
Wenn die Informationen nicht ausreichen, sage es ehrlich.
Gib immer die Quellen an, die du verwendet hast."""


class ChatService:
    """Service for handling chat interactions with Azure OpenAI."""

    def __init__(
        self,
        client: AsyncAzureOpenAI,
        settings: Settings,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the chat service.

        Args:
            client: Azure OpenAI client
            settings: Application settings
            http_client: HTTP client for calling other services
        """
        self._client = client
        self._settings = settings
        self._http_client = http_client

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
        if use_rag and self._http_client:
            # Use RAG: retrieve relevant documents first
            thoughts.append({"title": "Searching knowledge base", "description": ""})

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
                    "description": f"Found {len(search_results)} relevant documents",
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
            # Standard chat without RAG
            chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        chat_messages.extend(messages)

        # Generate response
        response = await self._client.chat.completions.create(
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

        # Stream response
        stream = await self._client.chat.completions.create(
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
        prompt = f"""Basierend auf dieser Konversation, generiere 3 kurze Folgefragen.
Antwort: {response}
Gib nur die Fragen zurueck, eine pro Zeile, ohne Nummerierung."""

        followup_response = await self._client.chat.completions.create(
            model=self._settings.azure_openai_deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200,
        )

        content = followup_response.choices[0].message.content or ""
        return [q.strip() for q in content.strip().split("\n") if q.strip()][:3]

