from __future__ import annotations

from app.poker.events import HandEvent
from app.poker.snapshot import PlayerSnapshot, TableSnapshot


def _player_map(snapshot: TableSnapshot) -> dict[str, PlayerSnapshot]:
    return {player.player_id: player for player in snapshot.players}


def _bet_amount(player: PlayerSnapshot) -> float:
    return player.current_bet.chips or 0.0


def _player_confidence(current: PlayerSnapshot, previous: PlayerSnapshot | None = None) -> float:
    if previous is None:
        return current.confidence
    return round(min(current.confidence, previous.confidence), 3)


def diff_snapshots(
    previous: TableSnapshot | None,
    current: TableSnapshot,
    *,
    starting_sequence_no: int = 1,
) -> list[HandEvent]:
    events: list[HandEvent] = []
    sequence_no = starting_sequence_no
    hand_id = current.hand_id or f"{current.table_id}:unknown-hand"

    if previous is None or previous.hand_id != current.hand_id:
        events.append(
            HandEvent(
                hand_id=hand_id,
                sequence_no=sequence_no,
                street=current.street,
                event_type="hand_started",
                pot_after=current.pot.chips,
                board_cards=current.board_cards,
                metadata={
                    "table_id": current.table_id,
                    "table_size": current.table_size,
                },
                confidence=current.confidence,
                timestamp=current.timestamp,
            )
        )
        sequence_no += 1

    if previous is not None and previous.street != current.street:
        events.append(
            HandEvent(
                hand_id=hand_id,
                sequence_no=sequence_no,
                street=current.street,
                event_type="street_changed",
                pot_after=current.pot.chips,
                board_cards=current.board_cards,
                confidence=min(previous.confidence, current.confidence),
                timestamp=current.timestamp,
            )
        )
        sequence_no += 1

    previous_players = _player_map(previous) if previous is not None else {}

    for player in current.players:
        previous_player = previous_players.get(player.player_id)
        current_bet = _bet_amount(player)
        previous_bet = _bet_amount(previous_player) if previous_player is not None else 0.0

        if previous_player is not None:
            if previous_player.in_hand is not False and player.in_hand is False:
                events.append(
                    HandEvent(
                        hand_id=hand_id,
                        sequence_no=sequence_no,
                        street=current.street,
                        actor_id=player.player_id,
                        event_type="player_folded",
                        pot_after=current.pot.chips,
                        confidence=_player_confidence(player, previous_player),
                        timestamp=current.timestamp,
                    )
                )
                sequence_no += 1
                continue

            if (
                previous_player.is_acting is True
                and player.is_acting is False
                and previous_bet == current_bet == 0
                and player.in_hand is not False
            ):
                events.append(
                    HandEvent(
                        hand_id=hand_id,
                        sequence_no=sequence_no,
                        street=current.street,
                        actor_id=player.player_id,
                        event_type="player_checked",
                        pot_after=current.pot.chips,
                        confidence=_player_confidence(player, previous_player),
                        timestamp=current.timestamp,
                    )
                )
                sequence_no += 1
                continue

            if current_bet > previous_bet:
                highest_previous_bet = max(
                    (_bet_amount(existing_player) for existing_player in previous.players),
                    default=0.0,
                )
                event_type = (
                    "player_called"
                    if previous_bet < highest_previous_bet and current_bet <= highest_previous_bet
                    else "player_raised"
                    if current_bet > highest_previous_bet > 0
                    else "player_bet"
                )

                events.append(
                    HandEvent(
                        hand_id=hand_id,
                        sequence_no=sequence_no,
                        street=current.street,
                        actor_id=player.player_id,
                        event_type=event_type,
                        amount_chips=round(current_bet - previous_bet, 3),
                        pot_after=current.pot.chips,
                        confidence=_player_confidence(player, previous_player),
                        timestamp=current.timestamp,
                    )
                )
                sequence_no += 1

    return events
