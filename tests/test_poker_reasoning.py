from app.poker.profiles import OpponentProfile
from app.poker.snapshot import PlayerSnapshot, StackAmount, TableSnapshot
from app.services.context_builder import build_decision_context
from app.services.event_diff import diff_snapshots
from app.services.state_reducer import apply_events, initialize_state_from_snapshot


def make_snapshot(
    *,
    street: str,
    pot: float,
    hero_bet: float,
    villain_bet: float,
    villain_in_hand: bool = True,
    hero_acting: bool = False,
    villain_acting: bool = False,
) -> TableSnapshot:
    return TableSnapshot(
        table_id="table-1",
        hand_id="hand-42",
        table_size=2,
        street=street,
        board_cards=["Ah", "8d", "4c"] if street != "preflop" else [],
        pot=StackAmount(chips=pot, raw_text=str(pot)),
        players=[
            PlayerSnapshot(
                player_id="hero",
                seat_label="BTN",
                stack=StackAmount(chips=97.5, bb=97.5, raw_text="97.5"),
                current_bet=StackAmount(chips=hero_bet, bb=hero_bet, raw_text=str(hero_bet)),
                in_hand=True,
                is_hero=True,
                is_acting=hero_acting,
                confidence=0.99,
            ),
            PlayerSnapshot(
                player_id="villain",
                seat_label="BB",
                stack=StackAmount(chips=100.0, bb=100.0, raw_text="100"),
                current_bet=StackAmount(
                    chips=villain_bet,
                    bb=villain_bet,
                    raw_text=str(villain_bet),
                ),
                in_hand=villain_in_hand,
                is_acting=villain_acting,
                confidence=0.98,
            ),
        ],
        legal_actions=["fold", "call", "raise"],
        heroToCall=StackAmount(chips=max(villain_bet - hero_bet, 0), raw_text="0"),
        confidence=0.97,
        sourceSurface="monitor",
    )


def test_diff_snapshots_emits_call_and_fold_events() -> None:
    previous = make_snapshot(
        street="preflop",
        pot=3.5,
        hero_bet=2.5,
        villain_bet=0,
        villain_acting=True,
    )
    current_call = make_snapshot(
        street="preflop",
        pot=5.0,
        hero_bet=2.5,
        villain_bet=2.5,
    )
    current_fold = make_snapshot(
        street="flop",
        pot=5.0,
        hero_bet=0,
        villain_bet=0,
        villain_in_hand=False,
    )

    call_events = diff_snapshots(previous, current_call, starting_sequence_no=2)
    fold_events = diff_snapshots(current_call, current_fold, starting_sequence_no=3)

    assert [event.event_type for event in call_events] == ["player_called"]
    assert call_events[0].amount_chips == 2.5
    assert [event.event_type for event in fold_events] == ["street_changed", "player_folded"]


def test_reducer_and_context_builder_track_history_over_time() -> None:
    initial = make_snapshot(
        street="preflop",
        pot=3.5,
        hero_bet=2.5,
        villain_bet=0,
        villain_acting=True,
    )
    next_snapshot = make_snapshot(
        street="preflop",
        pot=5.0,
        hero_bet=2.5,
        villain_bet=2.5,
    )

    state = initialize_state_from_snapshot(initial)
    events = diff_snapshots(initial, next_snapshot, starting_sequence_no=1)
    reduced = apply_events(state, events)

    profile = OpponentProfile(
        player_id="villain",
        hands_observed=84,
        vpip_est=29,
        pfr_est=21,
        aggression_note="Turn aggression slightly elevated",
    )
    context = build_decision_context(
        reduced,
        hero_cards=["As", "Kd"],
        opponent_profiles=[profile],
    )

    assert reduced.action_history == ["villain called 2.5"]
    assert reduced.players["villain"].contributed_total == 2.5
    assert context.hero["hole_cards"] == ["As", "Kd"]
    assert context.hand_history == ["villain called 2.5"]
    assert context.opponent_profiles[0].summary[1] == "VPIP/PFR approx 29/21"
