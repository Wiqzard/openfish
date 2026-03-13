from __future__ import annotations

from typing import Literal, cast

from app.errors import AppError
from app.poker.solver import SolverSpotConfig
from app.poker.state import HandState

DEFAULT_BET_SIZING_LINES = [
    "set_bet_sizes oop,flop,bet,50",
    "set_bet_sizes oop,flop,raise,60",
    "set_bet_sizes oop,flop,allin",
    "set_bet_sizes ip,flop,bet,50",
    "set_bet_sizes ip,flop,raise,60",
    "set_bet_sizes ip,flop,allin",
    "set_bet_sizes oop,turn,bet,50",
    "set_bet_sizes oop,turn,raise,60",
    "set_bet_sizes oop,turn,allin",
    "set_bet_sizes ip,turn,bet,50",
    "set_bet_sizes ip,turn,raise,60",
    "set_bet_sizes ip,turn,allin",
    "set_bet_sizes oop,river,bet,50",
    "set_bet_sizes oop,river,donk,50",
    "set_bet_sizes oop,river,raise,60,100",
    "set_bet_sizes oop,river,allin",
    "set_bet_sizes ip,river,bet,50",
    "set_bet_sizes ip,river,raise,60,100",
    "set_bet_sizes ip,river,allin",
]

PostflopStreet = Literal["flop", "turn", "river"]


def _effective_stack(state: HandState) -> float:
    stacks = [
        player.stack_current for player in state.players.values() if player.in_hand and player.stack_current is not None
    ]
    if not stacks:
        raise AppError(
            "SOLVER_STATE_ERROR",
            "Could not determine an effective stack from the current hand state.",
        )
    return round(min(stacks), 3)


def build_solver_spot_from_state(
    state: HandState,
    *,
    hero_cards: list[str],
    hero_position: str,
    ip_range: str,
    oop_range: str,
    bet_sizing_lines: list[str] | None = None,
) -> SolverSpotConfig:
    if state.street not in {"flop", "turn", "river"}:
        raise AppError(
            "SOLVER_UNSUPPORTED_STREET",
            "TexasSolver integration currently supports postflop streets only.",
        )
    street = cast(PostflopStreet, state.street)

    if hero_position != "oop":
        raise AppError(
            "SOLVER_NODE_PATH_UNSUPPORTED",
            (
                "Current TexasSolver integration only supports root-node street-entry "
                "spots where hero is OOP. IP decisions require child-node traversal, "
                "which is not implemented yet."
            ),
        )

    if state.pot_chips is None:
        raise AppError(
            "SOLVER_STATE_ERROR",
            "The current hand state does not include a visible pot size.",
        )

    return SolverSpotConfig(
        table_id=state.table_id,
        hand_id=state.hand_id,
        street=street,
        board_cards=state.board_cards,
        pot_chips=state.pot_chips,
        effective_stack_chips=_effective_stack(state),
        hero_position="ip" if hero_position == "ip" else "oop",
        hero_cards=hero_cards,
        ip_range=ip_range,
        oop_range=oop_range,
        bet_sizing_lines=bet_sizing_lines or DEFAULT_BET_SIZING_LINES,
        action_history=state.action_history,
    )


def render_texassolver_input(spot: SolverSpotConfig) -> str:
    lines = [
        f"set_pot {spot.pot_chips:g}",
        f"set_effective_stack {spot.effective_stack_chips:g}",
        f"set_board {','.join(spot.board_cards)}",
        f"set_range_ip {spot.ip_range}",
        f"set_range_oop {spot.oop_range}",
        *spot.bet_sizing_lines,
        f"set_allin_threshold {spot.allin_threshold}",
        "build_tree",
        f"set_thread_num {spot.thread_num}",
        f"set_accuracy {spot.accuracy}",
        f"set_max_iteration {spot.max_iteration}",
        f"set_print_interval {spot.print_interval}",
        "set_use_isomorphism 1",
        "start_solve",
        f"set_dump_rounds {spot.dump_rounds}",
        "dump_result output_result.json",
    ]
    return "\n".join(lines) + "\n"
