from app.errors import AppError
from app.parser import parse_plan_suggestion


def test_parse_plan_suggestion_from_raw_json() -> None:
    plan = parse_plan_suggestion(
        """
        {
          "summary": "The view is ready.",
          "current_view": "Baseline screen",
          "goals": ["Capture a screenshot"],
          "next_steps": ["Review the plan"],
          "risks": ["Mock mode"],
          "confidence": 0.72
        }
        """
    )

    assert plan.current_view == "Baseline screen"
    assert plan.confidence == 0.72


def test_parse_plan_suggestion_rejects_invalid_schema() -> None:
    try:
        parse_plan_suggestion(
            """
            {
              "summary": "Bad confidence",
              "current_view": "Debug",
              "goals": ["Test"],
              "next_steps": ["Fix"],
              "risks": ["Validation failure"],
              "confidence": 4
            }
            """
        )
    except AppError as exc:
        assert exc.code == "VLM_SCHEMA_ERROR"
    else:
        raise AssertionError("Expected AppError to be raised.")
