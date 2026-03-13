from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.poker.solver import SolverSpotConfig
from app.services.texassolver_wrapper import solve_with_texassolver


REPO_ROOT = Path(__file__).resolve().parents[1]
TEXASSOLVER_BIN = REPO_ROOT / "TexasSolver" / "console_solver"
TEXASSOLVER_RESOURCES = REPO_ROOT / "TexasSolver" / "resources"


pytestmark = pytest.mark.skipif(
    not TEXASSOLVER_BIN.exists() or not TEXASSOLVER_RESOURCES.exists(),
    reason="Local TexasSolver binary/resources are not available.",
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_live_texassolver_wrapper_returns_real_recommendation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cache_dir = tmp_path / "solver-cache"
    run_dir = tmp_path / "solver-runs"

    monkeypatch.setenv("SOLVER_MODE", "texassolver")
    monkeypatch.setenv("TEXASSOLVER_BIN", str(TEXASSOLVER_BIN))
    monkeypatch.setenv("TEXASSOLVER_RESOURCE_DIR", str(TEXASSOLVER_RESOURCES))
    monkeypatch.setenv("SOLVER_TIMEOUT_MS", "120000")
    monkeypatch.setenv("SOLVER_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("SOLVER_WORK_DIR", str(run_dir))

    spot = SolverSpotConfig(
        table_id="table-live",
        hand_id="hand-live",
        street="flop",
        board_cards=["Ah", "8d", "4c"],
        pot_chips=5.5,
        effective_stack_chips=20.0,
        hero_position="oop",
        hero_cards=["Kd", "Qc"],
        ip_range="AA,KK,QQ,JJ,TT,99,AK,AQ,AJ,KQ",
        oop_range="QQ,JJ,TT,99,88,77,AQ,AJ,AT,KQ,QJ,JT",
        thread_num=1,
        accuracy=5.0,
        max_iteration=20,
        print_interval=10,
        dump_rounds=1,
    )

    recommendation = await solve_with_texassolver(spot)

    assert recommendation.mode == "texassolver"
    assert recommendation.action
    assert recommendation.combo_key == "KdQc"
    assert recommendation.used_cached_result is False
    assert (cache_dir / spot.cache_key() / "output_result.json").exists()


@pytest.mark.anyio
async def test_live_texassolver_wrapper_uses_cache_on_second_call(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cache_dir = tmp_path / "solver-cache"
    run_dir = tmp_path / "solver-runs"

    monkeypatch.setenv("SOLVER_MODE", "texassolver")
    monkeypatch.setenv("TEXASSOLVER_BIN", str(TEXASSOLVER_BIN))
    monkeypatch.setenv("TEXASSOLVER_RESOURCE_DIR", str(TEXASSOLVER_RESOURCES))
    monkeypatch.setenv("SOLVER_TIMEOUT_MS", "120000")
    monkeypatch.setenv("SOLVER_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("SOLVER_WORK_DIR", str(run_dir))

    spot = SolverSpotConfig(
        table_id="table-live",
        hand_id="hand-live-cache",
        street="flop",
        board_cards=["Ah", "8d", "4c"],
        pot_chips=5.5,
        effective_stack_chips=20.0,
        hero_position="oop",
        hero_cards=["Kd", "Qc"],
        ip_range="AA,KK,QQ,JJ,TT,99,AK,AQ,AJ,KQ",
        oop_range="QQ,JJ,TT,99,88,77,AQ,AJ,AT,KQ,QJ,JT",
        thread_num=1,
        accuracy=5.0,
        max_iteration=20,
        print_interval=10,
        dump_rounds=1,
    )

    first = await solve_with_texassolver(spot)
    cached_file = cache_dir / spot.cache_key() / "output_result.json"
    assert cached_file.exists()

    cached_payload = json.loads(cached_file.read_text())
    assert "strategy" in cached_payload

    second = await solve_with_texassolver(spot)
    assert first.combo_key == second.combo_key
    assert second.used_cached_result is True
