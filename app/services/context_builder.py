from __future__ import annotations

from app.poker.context import DecisionContext, OpponentProfileContext, PlayerContext
from app.poker.profiles import OpponentProfile
from app.poker.state import HandState


def _profile_summary(profile: OpponentProfile) -> list[str]:
    summary = [f"{profile.hands_observed} hands observed"]

    if profile.vpip_est is not None and profile.pfr_est is not None:
        summary.append(f"VPIP/PFR approx {profile.vpip_est:.0f}/{profile.pfr_est:.0f}")
    if profile.three_bet_est is not None:
        summary.append(f"3-bet approx {profile.three_bet_est:.0f}%")
    if profile.fold_to_cbet_est is not None:
        summary.append(f"Fold to c-bet approx {profile.fold_to_cbet_est:.0f}%")
    if profile.aggression_note:
        summary.append(profile.aggression_note)
    summary.extend(profile.notes)
    return summary


def build_decision_context(
    state: HandState,
    *,
    hero_cards: list[str] | None = None,
    opponent_profiles: list[OpponentProfile] | None = None,
) -> DecisionContext:
    hero_state = None
    player_contexts: list[PlayerContext] = []
    for player in state.players.values():
        context = PlayerContext(
            player_id=player.player_id,
            position=player.position,
            stack_chips=player.stack_current,
            in_hand=player.in_hand,
            is_hero=player.is_hero,
        )
        player_contexts.append(context)
        if player.is_hero:
            hero_state = player

    hero_payload = {
        "player_id": hero_state.player_id if hero_state else None,
        "position": hero_state.position if hero_state else None,
        "hole_cards": hero_cards,
        "stack_chips": hero_state.stack_current if hero_state else None,
        "stack_bb": None,
    }

    profiles_payload: list[OpponentProfileContext] = []
    for profile in opponent_profiles or []:
        profiles_payload.append(
            OpponentProfileContext(
                player_id=profile.player_id,
                summary=_profile_summary(profile),
            )
        )

    return DecisionContext(
        snapshot_summary={
            "street": state.street,
            "board": state.board_cards,
            "pot_chips": state.pot_chips,
            "to_call_chips": state.to_call_chips,
            "legal_actions": state.legal_actions,
        },
        hero=hero_payload,
        players=player_contexts,
        hand_history=state.action_history,
        opponent_profiles=profiles_payload,
        uncertainties=state.uncertainties,
    )
