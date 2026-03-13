from __future__ import annotations

from app.agent.tools import (
    build_decision_context_tool,
    compute_pot_odds,
    get_current_hand_state,
    get_opponent_profiles,
    record_tool_call,
    solve_spot_tool,
)
from app.poker.solver import DecisionRequest, DecisionResponse
from app.services.solver_builder import build_solver_spot_from_state


async def decide_with_tools(request: DecisionRequest) -> DecisionResponse:
    tool_trace = []

    state_payload = get_current_hand_state(request.state)
    tool_trace.append(
        record_tool_call(
            "get_current_hand_state",
            {"hand_id": request.state.hand_id},
            {
                "street": state_payload["street"],
                "pot_chips": state_payload["pot_chips"],
                "players": len(state_payload["players"]),
            },
        )
    )

    profiles_payload = get_opponent_profiles(request.opponent_profiles)
    tool_trace.append(
        record_tool_call(
            "get_opponent_profiles",
            {"count": len(request.opponent_profiles)},
            {"player_ids": [profile["player_id"] for profile in profiles_payload]},
        )
    )

    context = build_decision_context_tool(
        request.state,
        hero_cards=request.hero_cards,
        opponent_profiles=request.opponent_profiles,
    )
    tool_trace.append(
        record_tool_call(
            "build_decision_context",
            {"hero_cards": request.hero_cards},
            {
                "hand_history_entries": len(context.hand_history),
                "uncertainties": len(context.uncertainties),
            },
        )
    )

    pot_odds = compute_pot_odds(
        to_call=request.state.to_call_chips,
        pot_before_call=request.state.pot_chips,
    )
    tool_trace.append(
        record_tool_call(
            "compute_pot_odds",
            {
                "to_call": request.state.to_call_chips,
                "pot_before_call": request.state.pot_chips,
            },
            pot_odds,
        )
    )

    solver_spot = build_solver_spot_from_state(
        request.state,
        hero_cards=request.hero_cards,
        hero_position=request.hero_position,
        ip_range=request.ip_range,
        oop_range=request.oop_range,
        bet_sizing_lines=request.bet_sizing_lines,
    )
    tool_trace.append(
        record_tool_call(
            "build_solver_spot_from_state",
            {
                "street": solver_spot.street,
                "hero_position": solver_spot.hero_position,
            },
            {
                "cache_key": solver_spot.cache_key(),
                "effective_stack_chips": solver_spot.effective_stack_chips,
            },
        )
    )

    solver_recommendation = await solve_spot_tool(solver_spot)
    tool_trace.append(
        record_tool_call(
            "solve_spot",
            {"cache_key": solver_spot.cache_key()},
            {
                "action": solver_recommendation.action,
                "frequency": solver_recommendation.frequency,
                "mode": solver_recommendation.mode,
                "used_cached_result": solver_recommendation.used_cached_result,
            },
        )
    )

    return DecisionResponse(
        context=context,
        solver_spot=solver_spot,
        solver_recommendation=solver_recommendation,
        tool_trace=tool_trace,
    )
