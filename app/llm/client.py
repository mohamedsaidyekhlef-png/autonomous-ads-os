"""LLM transport supporting local Ollama and OpenAI-compatible hosted APIs."""

import json
from typing import Any

import httpx

from app.core.settings import get_settings


def _structured_payload(
    system_prompt: str, command: str, context: dict[str, Any], schema: dict[str, Any]
) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "customer_command": command,
                        "verified_context": context,
                        "required_behavior": {
                            "mode": "shadow",
                            "do_not_invent_metrics": True,
                            "do_not_claim_execution": True,
                        },
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.1,
    }


async def structured_completion(
    system_prompt: str,
    command: str,
    context: dict[str, Any],
    schema: dict[str, Any],
) -> str:
    settings = get_settings()
    payload = _structured_payload(system_prompt, command, context, schema)
    provider = settings.llm_provider.lower()
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        if provider == "ollama":
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "stream": False,
                    "think": False,
                    "format": schema,
                    "options": {"temperature": 0.1},
                    "messages": payload["messages"],
                },
            )
            response.raise_for_status()
            return str(response.json()["message"]["content"])
        base_url = (settings.llm_base_url or "").rstrip("/")
        model = settings.llm_model or settings.ollama_model
        if not base_url or not settings.llm_api_key:
            raise RuntimeError("Hosted LLM configuration is incomplete.")
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={
                "model": model,
                "messages": payload["messages"],
                "temperature": 0.1,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "command_result",
                        "schema": schema,
                        "strict": True,
                    },
                },
            },
        )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"])
