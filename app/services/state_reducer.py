from __future__ import annotations

from app.poker.events import HandEvent
from app.poker.snapshot import TableSnapshot
from app.poker.state import HandState, PlayerState


def initialize_state_from_snapshot(snapshot: TableSnapshot) -> HandState:
    hero = next((player for player in snapshot.players if player.is_hero), None)
    acting = next((player for player in snapshot.players if player.is_acting), None)

    players = {
        player.player_id: PlayerState(
            player_id=player.player_id,
            seat_label=player.seat_label,
            is_hero=player.is_hero,
            stack_start=player.stack.chips,
            stack_current=player.stack.chips,
            contributed_this_round=player.current_bet.chips or 0,
            contributed_total=player.current_bet.chips or 0,
            in_hand=player.in_hand is not False,
            all_in=(player.stack.chips or 0) == 0 if player.stack.chips is not None else False,
        )
        for player in snapshot.players
    }

    uncertainties: list[str] = []
    for player in snapshot.players:
        if player.stack.chips is None and player.stack.raw_text:
            uncertainties.append(
                f"Stack for {player.player_id} is only available as raw text: {player.stack.raw_text}"
            )

    return HandState(
        hand_id=snapshot.hand_id or f"{snapshot.table_id}:unknown-hand",
        table_id=snapshot.table_id,
        table_size=snapshot.table_size,
        street=snapshot.street,
        board_cards=snapshot.board_cards,
        pot_chips=snapshot.pot.chips,
        hero_player_id=hero.player_id if hero else None,
        active_player_id=acting.player_id if acting else None,
        legal_actions=snapshot.legal_actions,
        to_call_chips=snapshot.hero_to_call.chips,
        players=players,
        uncertainties=uncertainties,
    )


def _history_line(event: HandEvent) -> str:
    actor = event.actor_id or "system"
    if event.event_type == "hand_started":
        return f"Hand started on {event.street}"
    if event.event_type == "street_changed":
        return f"Street changed to {event.street}"
    if event.event_type == "player_folded":
        return f"{actor} folded"
    if event.event_type == "player_checked":
        return f"{actor} checked"
    if event.event_type == "player_called":
        amount = event.amount_chips or 0
        return f"{actor} called {amount:g}"
    if event.event_type == "player_bet":
        amount = event.amount_chips or 0
        return f"{actor} bet {amount:g}"
    if event.event_type == "player_raised":
        amount = event.amount_chips or 0
        return f"{actor} raised by {amount:g}"
    return f"{actor} {event.event_type}"


def apply_events(state: HandState, events: list[HandEvent]) -> HandState:
    next_state = state.model_copy(deep=True)

    for event in events:
        if event.event_type == "hand_started":
            next_state.hand_id = event.hand_id
            next_state.street = event.street
            next_state.board_cards = event.board_cards
            next_state.pot_chips = event.pot_after
            next_state.action_history = []
            for player in next_state.players.values():
                player.contributed_this_round = 0
                player.contributed_total = 0
                player.in_hand = True
            continue

        if event.event_type == "street_changed":
            next_state.street = event.street
            next_state.board_cards = event.board_cards
            next_state.pot_chips = event.pot_after
            for player in next_state.players.values():
                player.contributed_this_round = 0
            next_state.action_history.append(_history_line(event))
            continue

        if event.actor_id is None:
            continue

        player = next_state.players.get(event.actor_id)
        if player is None:
            continue

        if event.event_type == "player_folded":
            player.in_hand = False
        elif event.event_type in {"player_called", "player_bet", "player_raised"}:
            amount = event.amount_chips or 0
            player.contributed_this_round += amount
            player.contributed_total += amount
            if player.stack_current is not None:
                player.stack_current = max(player.stack_current - amount, 0)
                player.all_in = player.stack_current == 0
        elif event.event_type == "player_checked":
            pass

        next_state.pot_chips = event.pot_after if event.pot_after is not None else next_state.pot_chips
        next_state.action_history.append(_history_line(event))

    return next_state
