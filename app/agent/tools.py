from __future__ import annotations

from typing import Any

from app.poker.context import DecisionContext
from app.poker.profiles import OpponentProfile
from app.poker.solver import SolverRecommendation, SolverSpotConfig, ToolCallRecord
from app.poker.state import HandState
from app.services.context_builder import build_decision_context
from app.services.texassolver_wrapper import solve_with_texassolver


def compute_pot_odds(*, to_call: float | None, pot_before_call: float | None) -> dict[str, float | None]:
    if to_call is None or pot_before_call is None:
        return {"pot_odds": None, "break_even_equity": None}

    if to_call <= 0:
        return {"pot_odds": 0.0, "break_even_equity": 0.0}

    total = pot_before_call + to_call
    return {
        "pot_odds": round(pot_before_call / to_call, 4),
        "break_even_equity": round(to_call / total, 4),
    }


def get_current_hand_state(state: HandState) -> dict[str, Any]:
    return state.model_dump()


def get_opponent_profiles(opponent_profiles: list[OpponentProfile]) -> list[dict[str, Any]]:
    return [profile.model_dump() for profile in opponent_profiles]


def build_decision_context_tool(
    state: HandState,
    *,
    hero_cards: list[str],
    opponent_profiles: list[OpponentProfile],
) -> DecisionContext:
    return build_decision_context(
        state,
        hero_cards=hero_cards,
        opponent_profiles=opponent_profiles,
    )


async def solve_spot_tool(spot: SolverSpotConfig) -> SolverRecommendation:
    return await solve_with_texassolver(spot)


def record_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    summary: dict[str, Any],
) -> ToolCallRecord:
    return ToolCallRecord(tool_name=tool_name, arguments=arguments, summary=summary)
