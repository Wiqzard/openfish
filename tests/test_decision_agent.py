from fastapi.testclient import TestClient

from app.main import app
from app.poker.profiles import OpponentProfile

client = TestClient(app)


def test_decide_endpoint_returns_mock_solver_recommendation() -> None:
    response = client.post(
        "/api/decide",
        json={
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
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["solver_recommendation"]["action"] == "BET 50"
    assert payload["solver_recommendation"]["normalized_action"] == "bet"
    assert payload["solver_recommendation"]["mode"] == "mock"
    assert payload["tool_trace"][-1]["tool_name"] == "solve_spot"
    assert payload["context"]["hero"]["hole_cards"] == ["As", "Kd"]


def test_decide_endpoint_rejects_preflop_solver_request() -> None:
    response = client.post(
        "/api/decide",
        json={
            "state": {
                "hand_id": "hand-10",
                "table_id": "table-1",
                "table_size": 2,
                "street": "preflop",
                "board_cards": [],
                "pot_chips": 3.0,
                "hero_player_id": "hero",
                "active_player_id": "hero",
                "legal_actions": ["fold", "call", "raise"],
                "to_call_chips": 1.0,
                "min_raise_chips": 3.0,
                "players": {
                    "hero": {
                        "player_id": "hero",
                        "is_hero": True,
                        "stack_current": 99,
                        "in_hand": True,
                        "all_in": False,
                    },
                    "villain": {
                        "player_id": "villain",
                        "is_hero": False,
                        "stack_current": 100,
                        "in_hand": True,
                        "all_in": False,
                    },
                },
                "action_history": [],
                "uncertainties": [],
            },
            "hero_cards": ["As", "Kd"],
            "hero_position": "ip",
            "ip_range": "AA,KK,QQ,AK",
            "oop_range": "QQ,JJ,TT,AQ",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "SOLVER_UNSUPPORTED_STREET"


def test_decide_endpoint_rejects_ip_root_requests_until_node_traversal_exists() -> None:
    response = client.post(
        "/api/decide",
        json={
            "state": {
                "hand_id": "hand-50",
                "table_id": "table-1",
                "table_size": 2,
                "street": "flop",
                "board_cards": ["Ah", "8d", "4c"],
                "pot_chips": 5.5,
                "hero_player_id": "hero",
                "active_player_id": "villain",
                "legal_actions": ["call", "raise", "fold"],
                "to_call_chips": 2.0,
                "min_raise_chips": 6.0,
                "players": {
                    "hero": {
                        "player_id": "hero",
                        "is_hero": True,
                        "stack_current": 95,
                        "in_hand": True,
                        "all_in": False,
                    },
                    "villain": {
                        "player_id": "villain",
                        "is_hero": False,
                        "stack_current": 98,
                        "in_hand": True,
                        "all_in": False,
                    },
                },
                "action_history": ["hero checked", "villain bet 2"],
                "uncertainties": [],
            },
            "hero_cards": ["As", "Kd"],
            "hero_position": "ip",
            "ip_range": "AA,KK,QQ,AK",
            "oop_range": "QQ,JJ,TT,AQ",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "SOLVER_NODE_PATH_UNSUPPORTED"
