from __future__ import annotations

from pydantic import BaseModel, Field


class PlayerContext(BaseModel):
    player_id: str
    position: str | None = None
    stack_chips: float | None = None
    stack_bb: float | None = None
    in_hand: bool = True
    is_hero: bool = False


class OpponentProfileContext(BaseModel):
    player_id: str
    summary: list[str] = Field(default_factory=list)


class DecisionContext(BaseModel):
    task: str = "recommend_best_action"
    snapshot_summary: dict[str, object]
    hero: dict[str, object]
    players: list[PlayerContext]
    hand_history: list[str]
    opponent_profiles: list[OpponentProfileContext] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
