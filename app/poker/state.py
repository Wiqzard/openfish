from __future__ import annotations

from pydantic import BaseModel, Field

from app.poker.snapshot import Street


class PlayerState(BaseModel):
    player_id: str
    seat_label: str | None = None
    is_hero: bool = False
    stack_start: float | None = None
    stack_current: float | None = None
    contributed_this_round: float = 0
    contributed_total: float = 0
    in_hand: bool = True
    all_in: bool = False
    position: str | None = None


class HandState(BaseModel):
    hand_id: str
    table_id: str
    table_size: int | None = None
    street: Street = "unknown"
    board_cards: list[str] = Field(default_factory=list)
    pot_chips: float | None = None
    hero_player_id: str | None = None
    active_player_id: str | None = None
    legal_actions: list[str] = Field(default_factory=list)
    to_call_chips: float | None = None
    min_raise_chips: float | None = None
    players: dict[str, PlayerState] = Field(default_factory=dict)
    action_history: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
