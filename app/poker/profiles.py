from __future__ import annotations

from pydantic import BaseModel, Field


class OpponentProfile(BaseModel):
    player_id: str
    display_name: str | None = None
    hands_observed: int = 0
    vpip_est: float | None = None
    pfr_est: float | None = None
    three_bet_est: float | None = None
    fold_to_cbet_est: float | None = None
    aggression_note: str | None = None
    notes: list[str] = Field(default_factory=list)
