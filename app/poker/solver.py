from __future__ import annotations

import hashlib
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.poker.context import DecisionContext
from app.poker.profiles import OpponentProfile
from app.poker.state import HandState


SolverMode = Literal["mock", "texassolver"]


class SolverSpotConfig(BaseModel):
    table_id: str
    hand_id: str
    street: Literal["flop", "turn", "river"]
    board_cards: list[str]
    pot_chips: float
    effective_stack_chips: float
    hero_position: Literal["ip", "oop"]
    hero_cards: list[str] = Field(min_length=2, max_length=2)
    ip_range: str = Field(min_length=1)
    oop_range: str = Field(min_length=1)
    bet_sizing_lines: list[str] = Field(default_factory=list)
    action_history: list[str] = Field(default_factory=list)
    allin_threshold: float = Field(default=0.67, gt=0, lt=1)
    thread_num: int = Field(default=4, ge=1)
    accuracy: float = Field(default=0.5, gt=0)
    max_iteration: int = Field(default=200, ge=1)
    print_interval: int = Field(default=10, ge=1)
    dump_rounds: int = Field(default=2, ge=1)

    def cache_key(self) -> str:
        return hashlib.sha256(
            self.model_dump_json(by_alias=True, exclude_none=True).encode("utf-8")
        ).hexdigest()[:16]


class SolverRecommendation(BaseModel):
    action: str
    normalized_action: str
    frequency: float = Field(ge=0, le=1)
    action_frequencies: dict[str, float] = Field(default_factory=dict)
    combo_key: str
    notes: list[str] = Field(default_factory=list)
    mode: SolverMode
    used_cached_result: bool = False
    cache_key: str
    raw_output: dict[str, Any] | None = None


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)


class DecisionRequest(BaseModel):
    state: HandState
    hero_cards: list[str] = Field(min_length=2, max_length=2)
    hero_position: Literal["ip", "oop"]
    ip_range: str = Field(min_length=1)
    oop_range: str = Field(min_length=1)
    opponent_profiles: list[OpponentProfile] = Field(default_factory=list)
    bet_sizing_lines: list[str] = Field(default_factory=list)


class DecisionResponse(BaseModel):
    context: DecisionContext
    solver_spot: SolverSpotConfig
    solver_recommendation: SolverRecommendation
    tool_trace: list[ToolCallRecord] = Field(default_factory=list)
