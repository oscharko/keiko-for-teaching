"""Chat service for processing messages with Azure OpenAI."""

from typing import Any

from openai import AsyncAzureOpenAI

from ..config import Settings

SYSTEM_PROMPT = """Du bist Keiko, ein hilfreicher KI-Assistent fuer Wissensmanagement.
Antworte praezise und hilfreich auf Deutsch. Wenn du dir nicht sicher bist, sage es ehrlich."""


class ChatService:
    """Service for handling chat interactions with Azure OpenAI."""

    def __init__(self, client: AsyncAzureOpenAI, settings: Settings) -> None:
        """Initialize the chat service."""
        self._client = client
        self._settings = settings

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        suggest_followup: bool = True,
    ) -> dict[str, Any]:
        """Process chat messages and return AI response."""
        chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        chat_messages.extend(messages)

        response = await self._client.chat.completions.create(
            model=self._settings.azure_openai_deployment,
            messages=chat_messages,  # type: ignore[arg-type]
            temperature=temperature or self._settings.default_temperature,
            max_tokens=self._settings.default_max_tokens,
        )

        content = response.choices[0].message.content or ""
        result: dict[str, Any] = {"content": content, "thoughts": []}

        if suggest_followup:
            result["followup_questions"] = await self._generate_followup_questions(
                messages, content
            )

        return result

    async def _generate_followup_questions(
        self, messages: list[dict[str, str]], response: str
    ) -> list[str]:
        """Generate follow-up questions based on the conversation."""
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

