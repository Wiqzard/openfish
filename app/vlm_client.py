from __future__ import annotations

from typing import Any

import httpx

from app.config import get_config
from app.errors import AppError
from app.models import PlanSuggestion
from app.parser import parse_plan_suggestion

SYSTEM_PROMPT = """You are a visual planning assistant for a browser screenshot.
Return exactly one JSON object and no surrounding commentary.

Required JSON schema:
{
  "summary": string,
  "current_view": string,
  "goals": string[],
  "next_steps": string[],
  "risks": string[],
  "confidence": number
}

Rules:
- Keep the response concise.
- confidence must be a number between 0 and 1.
- If something is unclear, mention it in risks instead of inventing certainty.
- Do not wrap the JSON in markdown fences."""

MOCK_PLAN = PlanSuggestion(
    summary=(
        "The screenshot shows the Python-based OpenFish interface ready to analyze a selected monitor, window, or tab."
    ),
    current_view="OpenFish Python baseline home screen",
    goals=[
        "Capture the selected browser surface",
        "Send the screenshot through the Python VLM client",
    ],
    next_steps=[
        "Confirm the preview matches the intended source",
        "Review the structured plan before extending the workflow",
    ],
    risks=[
        "Mock mode is enabled, so no live VLM call has been made",
        "This branch keeps browser capture in JavaScript because web capture requires client APIs",
    ],
    confidence=0.57,
)


def _extract_message_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise AppError(
            "VLM_EMPTY_RESPONSE",
            "The VLM response did not contain any choices.",
            status_code=502,
        )

    content = choices[0].get("message", {}).get("content")

    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for item in content:
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                text_parts.append(text.strip())
        if text_parts:
            return "\n".join(text_parts)

    raise AppError(
        "VLM_EMPTY_RESPONSE",
        "The VLM response did not contain text content.",
        status_code=502,
    )


async def request_plan_suggestion(image_data_url: str) -> tuple[PlanSuggestion, str]:
    config = get_config()

    if config.base_url == "mock":
        raw = MOCK_PLAN.model_dump_json(indent=2)
        return MOCK_PLAN, raw

    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    payload = {
        "model": config.model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Analyze this browser screenshot and return the requested "
                            "JSON plan. Focus on what the user should do next."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ],
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=config.timeout_ms / 1000) as client:
            response = await client.post(
                f"{config.base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
    except httpx.TimeoutException as exc:
        raise AppError(
            "VLM_TIMEOUT",
            f"The VLM request timed out after {config.timeout_ms}ms.",
            status_code=504,
        ) from exc
    except httpx.HTTPError as exc:
        raise AppError(
            "VLM_NETWORK_ERROR",
            "The Python backend could not reach the VLM endpoint.",
            details=str(exc),
            status_code=502,
        ) from exc

    response_text = response.text
    if response.status_code >= 400:
        raise AppError(
            "VLM_HTTP_ERROR",
            f"The VLM request failed with {response.status_code} {response.reason_phrase}.",
            raw_response=response_text,
            status_code=502,
        )

    try:
        parsed = response.json()
    except ValueError as exc:
        raise AppError(
            "VLM_BAD_JSON",
            "The VLM returned invalid JSON.",
            raw_response=response_text,
            status_code=502,
        ) from exc

    raw_message = _extract_message_text(parsed)
    plan = parse_plan_suggestion(raw_message)
    return plan, raw_message
