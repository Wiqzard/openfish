from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    base_url: str
    api_key: str | None
    model: str
    timeout_ms: int
    solver_mode: str
    texassolver_bin: str | None
    texassolver_resource_dir: str | None
    solver_timeout_ms: int
    solver_cache_dir: str
    solver_work_dir: str


def _parse_timeout(value: str | None) -> int:
    if value is None:
        return 20_000

    try:
        parsed = int(value)
    except ValueError:
        return 20_000

    return parsed if parsed > 0 else 20_000


def get_config() -> AppConfig:
    return AppConfig(
        base_url=os.getenv("VLM_BASE_URL", "mock").strip() or "mock",
        api_key=os.getenv("VLM_API_KEY", "").strip() or None,
        model=os.getenv("VLM_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini",
        timeout_ms=_parse_timeout(os.getenv("VLM_TIMEOUT_MS")),
        solver_mode=os.getenv("SOLVER_MODE", "mock").strip() or "mock",
        texassolver_bin=os.getenv("TEXASSOLVER_BIN", "").strip() or None,
        texassolver_resource_dir=os.getenv("TEXASSOLVER_RESOURCE_DIR", "").strip() or None,
        solver_timeout_ms=_parse_timeout(os.getenv("SOLVER_TIMEOUT_MS", "120000")),
        solver_cache_dir=os.getenv("SOLVER_CACHE_DIR", ".openfish/solver-cache").strip()
        or ".openfish/solver-cache",
        solver_work_dir=os.getenv("SOLVER_WORK_DIR", ".openfish/solver-runs").strip()
        or ".openfish/solver-runs",
    )
