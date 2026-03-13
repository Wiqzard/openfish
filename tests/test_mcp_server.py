import asyncio
import json

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from app.mcp_server import create_mcp_server
from app.poker.profiles import OpponentProfile


def _tool_payload(result: object) -> dict:
    if isinstance(result, tuple):
        _, structured_payload = result
        if isinstance(structured_payload, dict):
            return structured_payload
        result = result[0]

    assert isinstance(result, list)
    assert result
    text = getattr(result[0], "text", None)
    assert isinstance(text, str)
    return json.loads(text)


def _decision_request_payload() -> dict:
    return {
        "state": {
            "hand_id": "hand-42",
            "table_id": "table-1",
            "table_size": 2,
            "street": "flop",
            "board_cards": ["Ah", "8d", "4c"],
            "pot_chips": 5.5,
            "hero_player_id": "hero",
            "active_player_id": "hero",
            "legal_actions": ["check", "bet"],
            "to_call_chips": 0,
            "min_raise_chips": None,
            "players": {
                "hero": {
                    "player_id": "hero",
                    "seat_label": "BB",
                    "is_hero": True,
                    "stack_start": 97.5,
                    "stack_current": 97.5,
                    "contributed_this_round": 0,
                    "contributed_total": 2.5,
                    "in_hand": True,
                    "all_in": False,
                    "position": "BB",
                },
                "villain": {
                    "player_id": "villain",
                    "seat_label": "BTN",
                    "is_hero": False,
                    "stack_start": 100,
                    "stack_current": 100,
                    "contributed_this_round": 0,
                    "contributed_total": 2.5,
                    "in_hand": True,
                    "all_in": False,
                    "position": "BTN",
                },
            },
            "action_history": [
                "villain raised by 2.5",
                "hero called 2.5",
            ],
            "uncertainties": [],
        },
        "hero_cards": ["As", "Kd"],
        "hero_position": "oop",
        "ip_range": "AA,KK,QQ,AK,AQs,AJs,KQs",
        "oop_range": "QQ,JJ,TT,99,AQ,AJ,KQ,AK",
        "opponent_profiles": [
            OpponentProfile(
                player_id="villain",
                hands_observed=84,
                vpip_est=29,
                pfr_est=21,
                aggression_note="Turn aggression slightly elevated",
            ).model_dump()
        ],
    }


def test_mcp_server_lists_openfish_tools() -> None:
    server = create_mcp_server()

    tools = asyncio.run(server.list_tools())
    tool_names = {tool.name for tool in tools}

    assert "analyze_image" in tool_names
    assert "compute_pot_odds" in tool_names
    assert "build_solver_spot" in tool_names
    assert "solve_spot" in tool_names
    assert "decide_hand" in tool_names


def test_mcp_analyze_image_returns_valid_plan() -> None:
    server = create_mcp_server()

    result = asyncio.run(
        server.call_tool(
            "analyze_image",
            {
                "data_url": "data:image/png;base64,ZmFrZQ==",
                "width": 1440,
                "height": 900,
                "surface_type": "monitor",
            },
        )
    )
    payload = _tool_payload(result)

    assert payload["image"]["surfaceType"] == "monitor"
    assert payload["plan"]["summary"]
    assert payload["rawResponse"]


def test_mcp_decide_hand_returns_mock_solver_recommendation() -> None:
    server = create_mcp_server()

    result = asyncio.run(server.call_tool("decide_hand", {"request": _decision_request_payload()}))
    payload = _tool_payload(result)

    assert payload["solver_recommendation"]["action"] == "BET 50"
    assert payload["solver_recommendation"]["mode"] == "mock"
    assert payload["tool_trace"][-1]["tool_name"] == "solve_spot"


def test_mcp_build_solver_spot_surfaces_current_ip_limitation() -> None:
    server = create_mcp_server()
    request = _decision_request_payload()
    request["hero_position"] = "ip"

    with pytest.raises(ToolError, match="SOLVER_NODE_PATH_UNSUPPORTED"):
        asyncio.run(
            server.call_tool(
                "build_solver_spot",
                {
                    "state": request["state"],
                    "hero_cards": request["hero_cards"],
                    "hero_position": request["hero_position"],
                    "ip_range": request["ip_range"],
                    "oop_range": request["oop_range"],
                },
            )
        )
