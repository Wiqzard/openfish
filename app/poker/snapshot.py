from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Street = Literal["preflop", "flop", "turn", "river", "showdown", "unknown"]
SurfaceType = Literal["browser", "window", "monitor", "unknown"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StackAmount(BaseModel):
    chips: float | None = None
    bb: float | None = None
    raw_text: str | None = None


class PlayerSnapshot(BaseModel):
    player_id: str = Field(min_length=1)
    seat_label: str | None = None
    name: str | None = None
    stack: StackAmount = Field(default_factory=StackAmount)
    in_hand: bool | None = None
    sitting_out: bool | None = None
    hole_cards_visible: list[str] | None = None
    is_hero: bool = False
    is_dealer: bool | None = None
    is_acting: bool | None = None
    current_bet: StackAmount = Field(default_factory=StackAmount)
    confidence: float = Field(ge=0, le=1)


class TableSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    table_id: str = Field(min_length=1)
    hand_id: str | None = None
    table_size: int | None = Field(default=None, ge=2)
    street: Street = "unknown"
    board_cards: list[str] = Field(default_factory=list)
    pot: StackAmount = Field(default_factory=StackAmount)
    players: list[PlayerSnapshot]
    legal_actions: list[str] = Field(default_factory=list)
    hero_to_call: StackAmount = Field(alias="heroToCall", default_factory=StackAmount)
    timestamp: str = Field(default_factory=utc_now_iso)
    confidence: float = Field(ge=0, le=1)
    source_surface: SurfaceType = Field(alias="sourceSurface", default="unknown")

    @field_validator("players")
    @classmethod
    def validate_unique_players(cls, value: list[PlayerSnapshot]) -> list[PlayerSnapshot]:
        player_ids = [player.player_id for player in value]
        if len(player_ids) != len(set(player_ids)):
            raise ValueError("Each player snapshot must have a unique player_id.")
        return value
