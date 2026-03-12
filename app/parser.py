from __future__ import annotations

import json

from pydantic import ValidationError

from app.errors import AppError
from app.models import PlanSuggestion


def extract_json_candidate(raw: str) -> str:
    stripped = raw.strip()

    if stripped.startswith("```"):
        parts = stripped.split("```")
        if len(parts) >= 3:
            candidate = parts[1]
            if candidate.startswith("json"):
                candidate = candidate[4:]
            return candidate.strip()

    first_brace = raw.find("{")
    last_brace = raw.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
        raise AppError(
            "VLM_SCHEMA_ERROR",
            "No JSON object was found in the VLM response.",
            raw_response=raw,
            status_code=502,
        )

    return raw[first_brace : last_brace + 1]


def parse_plan_suggestion(raw: str) -> PlanSuggestion:
    try:
        candidate = extract_json_candidate(raw)
        parsed = json.loads(candidate)
        return PlanSuggestion.model_validate(parsed)
    except json.JSONDecodeError as exc:
        raise AppError(
            "VLM_BAD_JSON",
            "The VLM returned invalid JSON.",
            details=str(exc),
            raw_response=raw,
            status_code=502,
        ) from exc
    except ValidationError as exc:
        raise AppError(
            "VLM_SCHEMA_ERROR",
            "The VLM response did not match the expected plan schema.",
            details=str(exc),
            raw_response=raw,
            status_code=502,
        ) from exc
