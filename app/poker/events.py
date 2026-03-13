from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.poker.snapshot import Street

EventType = Literal[
    "hand_started",
    "street_changed",
    "player_folded",
    "player_checked",
    "player_called",
    "player_bet",
    "player_raised",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class HandEvent(BaseModel):
    hand_id: str = Field(min_length=1)
    sequence_no: int = Field(ge=1)
    street: Street
    actor_id: str | None = None
    event_type: EventType
    amount_chips: float | None = None
    pot_after: float | None = None
    board_cards: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)
    timestamp: str = Field(default_factory=utc_now_iso)
