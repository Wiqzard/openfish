from __future__ import annotations

import asyncio
import json
from typing import Any

import uvicorn
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str | list[dict[str, Any]]


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float | None = None


def _extract_user_text(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role != "user":
            continue
        if isinstance(message.content, str):
            return message.content
        text_parts = []
        for item in message.content:
            text = item.get("text")
            if isinstance(text, str):
                text_parts.append(text)
        return "\n".join(text_parts)
    return ""


def _default_plan(summary: str) -> dict[str, Any]:
    return {
        "summary": summary,
        "current_view": "Dummy VLM response",
        "goals": ["Validate the OpenFish integration", "Exercise the end-to-end pipeline"],
        "next_steps": ["Inspect the parsed JSON", "Switch scenarios to test error handling"],
        "risks": ["This is synthetic output", "No real visual reasoning is happening"],
        "confidence": 0.66,
    }


app = FastAPI(title="OpenFish Dummy VLM")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    x_dummy_vlm_scenario: str | None = Header(default=None),
) -> Response:
    scenario = (x_dummy_vlm_scenario or request.model or "dummy-plan").strip().lower()
    user_text = _extract_user_text(request.messages)

    if scenario in {"dummy-http-error", "http-error"}:
        return JSONResponse(status_code=500, content={"error": "dummy server failure"})

    if scenario in {"dummy-bad-json-body", "bad-json-body"}:
        return PlainTextResponse("{not valid json", status_code=200, media_type="application/json")

    if scenario in {"dummy-delay", "delay"}:
        await asyncio.sleep(0.25)

    if scenario in {"dummy-schema-error", "schema-error"}:
        content = json.dumps(
            {
                "summary": "This intentionally breaks the schema.",
                "current_view": "Bad schema",
                "goals": ["Trigger validation"],
                "next_steps": ["Inspect the error path"],
                "risks": ["Confidence is invalid"],
                "confidence": 4,
            }
        )
    elif scenario in {"dummy-text-array", "text-array"}:
        content = [
            {
                "type": "text",
                "text": json.dumps(
                    _default_plan(
                        f"Array-content response for: {user_text[:48] or 'no user text'}"
                    )
                ),
            }
        ]
    else:
        content = json.dumps(
            _default_plan(
                f"Dummy VLM analyzed the request: {user_text[:64] or 'no user text'}"
            )
        )

    return JSONResponse(
        {
            "id": "chatcmpl-dummy",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": "stop",
                }
            ],
        }
    )


def main() -> None:
    uvicorn.run("app.testing.dummy_vlm_server:app", host="127.0.0.1", port=8010, reload=False)


if __name__ == "__main__":
    main()
