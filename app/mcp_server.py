from __future__ import annotations

import argparse
from typing import Any, Literal, NoReturn

from mcp.server.fastmcp import FastMCP

from app.agent.tools import (
    build_decision_context_tool,
    compute_pot_odds,
    get_current_hand_state,
    get_opponent_profiles,
    solve_spot_tool,
)
from app.errors import AppError
from app.models import AnalysisRequest, AnalysisResult, CapturedImage
from app.poker.profiles import OpponentProfile
from app.poker.solver import DecisionRequest, SolverSpotConfig
from app.poker.state import HandState
from app.services.decision_agent import decide_with_tools
from app.services.solver_builder import build_solver_spot_from_state
from app.vlm_client import request_plan_suggestion


def _rethrow_tool_error(exc: AppError) -> NoReturn:
    detail_parts = [exc.code, exc.message]
    if exc.details:
        detail_parts.append(exc.details)
    raise ValueError(" | ".join(detail_parts)) from exc


def create_mcp_server() -> FastMCP:
    server = FastMCP(
        "OpenFish",
        instructions=(
            "Use these tools to analyze screenshots, build poker decision context, "
            "and consult TexasSolver-backed recommendations. Prefer tool calls over guessing."
        ),
    )

    @server.tool(
        name="analyze_image",
        description="Analyze a screenshot with the configured VLM and return the validated OpenFish planning response.",
    )
    async def analyze_image(
        data_url: str,
        width: int,
        height: int,
        surface_type: Literal["browser", "window", "monitor", "unknown"],
    ) -> dict[str, Any]:
        request = AnalysisRequest(
            image=CapturedImage(
                dataUrl=data_url,
                width=width,
                height=height,
                surfaceType=surface_type,
            )
        )
        try:
            plan, raw_response = await request_plan_suggestion(request.image.data_url)
        except AppError as exc:
            _rethrow_tool_error(exc)

        return AnalysisResult(
            image=request.image,
            plan=plan,
            rawResponse=raw_response,
        ).model_dump(by_alias=True)

    @server.tool(
        name="get_current_hand_state",
        description="Validate and normalize a canonical hand state payload.",
    )
    def get_current_hand_state_tool(state: dict[str, Any]) -> dict[str, Any]:
        parsed_state = HandState.model_validate(state)
        return get_current_hand_state(parsed_state)

    @server.tool(
        name="get_opponent_profiles",
        description="Return normalized opponent profile payloads for the provided players.",
    )
    def get_opponent_profiles_tool(opponent_profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        parsed_profiles = [OpponentProfile.model_validate(profile) for profile in opponent_profiles]
        return get_opponent_profiles(parsed_profiles)

    @server.tool(
        name="compute_pot_odds",
        description="Compute pot odds and break-even equity for a call decision.",
    )
    def compute_pot_odds_tool(
        to_call: float | None,
        pot_before_call: float | None,
    ) -> dict[str, float | None]:
        return compute_pot_odds(to_call=to_call, pot_before_call=pot_before_call)

    @server.tool(
        name="build_decision_context",
        description="Build the compact decision context the reasoning layer uses for history-aware poker decisions.",
    )
    def build_decision_context_mcp(
        state: dict[str, Any],
        hero_cards: list[str],
        opponent_profiles: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        parsed_state = HandState.model_validate(state)
        parsed_profiles = [OpponentProfile.model_validate(profile) for profile in opponent_profiles or []]
        return build_decision_context_tool(
            parsed_state,
            hero_cards=hero_cards,
            opponent_profiles=parsed_profiles,
        ).model_dump()

    @server.tool(
        name="build_solver_spot",
        description="Convert a canonical hand state into the current TexasSolver spot abstraction used by OpenFish.",
    )
    def build_solver_spot(
        state: dict[str, Any],
        hero_cards: list[str],
        hero_position: Literal["ip", "oop"],
        ip_range: str,
        oop_range: str,
        bet_sizing_lines: list[str] | None = None,
    ) -> dict[str, Any]:
        parsed_state = HandState.model_validate(state)
        try:
            spot = build_solver_spot_from_state(
                parsed_state,
                hero_cards=hero_cards,
                hero_position=hero_position,
                ip_range=ip_range,
                oop_range=oop_range,
                bet_sizing_lines=bet_sizing_lines,
            )
        except AppError as exc:
            _rethrow_tool_error(exc)

        return spot.model_dump()

    @server.tool(
        name="solve_spot",
        description="Run the current TexasSolver integration or mock solver for a provided solver spot payload.",
    )
    async def solve_spot(spot: dict[str, Any]) -> dict[str, Any]:
        parsed_spot = SolverSpotConfig.model_validate(spot)
        try:
            recommendation = await solve_spot_tool(parsed_spot)
        except AppError as exc:
            _rethrow_tool_error(exc)

        return recommendation.model_dump()

    @server.tool(
        name="decide_hand",
        description=(
            "Run the full OpenFish decision pipeline: context building, pot odds, "
            "solver spot creation, solver execution, and tool trace."
        ),
    )
    async def decide_hand(request: dict[str, Any]) -> dict[str, Any]:
        parsed_request = DecisionRequest.model_validate(request)
        try:
            decision = await decide_with_tools(parsed_request)
        except AppError as exc:
            _rethrow_tool_error(exc)
        return decision.model_dump()

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the OpenFish MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport to run. Default is stdio.",
    )
    args = parser.parse_args()
    create_mcp_server().run(transport=args.transport)


if __name__ == "__main__":
    main()
