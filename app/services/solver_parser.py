from __future__ import annotations

from typing import Any

from app.errors import AppError
from app.poker.solver import SolverRecommendation, SolverSpotConfig


def _combo_candidates(hero_cards: list[str]) -> list[str]:
    if len(hero_cards) != 2:
        return []
    first, second = hero_cards
    return [f"{first}{second}", f"{second}{first}"]


def _normalize_action(action: str) -> str:
    lowered = action.strip().lower()
    if lowered.startswith("bet"):
        return "bet"
    if lowered.startswith("raise"):
        return "raise"
    if lowered.startswith("call"):
        return "call"
    if lowered.startswith("check"):
        return "check"
    if lowered.startswith("fold"):
        return "fold"
    return lowered


def parse_root_solver_recommendation(
    output: dict[str, Any],
    spot: SolverSpotConfig,
    *,
    used_cached_result: bool,
    mode: str,
) -> SolverRecommendation:
    actions = output.get("actions") or output.get("strategy", {}).get("actions") or []
    strategy_blob = output.get("strategy", {})
    combo_strategies = strategy_blob.get("strategy", {})

    if not actions or not isinstance(combo_strategies, dict):
        raise AppError(
            "SOLVER_PARSE_ERROR",
            "TexasSolver output did not contain a root action strategy.",
            raw_response=str(output),
            status_code=502,
        )

    combo_key = None
    combo_strategy = None
    for candidate in _combo_candidates(spot.hero_cards):
        if candidate in combo_strategies:
            combo_key = candidate
            combo_strategy = combo_strategies[candidate]
            break

    if combo_key is None or not isinstance(combo_strategy, list):
        raise AppError(
            "SOLVER_COMBO_NOT_FOUND",
            "TexasSolver output did not contain strategy frequencies for the hero hole cards at the root node.",
            details=f"Hero cards: {spot.hero_cards}",
            status_code=502,
        )

    action_frequencies = {
        str(action): round(float(combo_strategy[index]), 6)
        for index, action in enumerate(actions)
        if index < len(combo_strategy)
    }

    best_action = max(action_frequencies.items(), key=lambda item: item[1])
    notes = []
    if spot.action_history:
        notes.append(
            (
                "Current implementation solves the root node for the provided street "
                "and does not yet traverse post-action child nodes."
            )
        )

    return SolverRecommendation(
        action=best_action[0],
        normalized_action=_normalize_action(best_action[0]),
        frequency=best_action[1],
        action_frequencies=action_frequencies,
        combo_key=combo_key,
        notes=notes,
        mode=mode,  # type: ignore[arg-type]
        used_cached_result=used_cached_result,
        cache_key=spot.cache_key(),
        raw_output=output,
    )
