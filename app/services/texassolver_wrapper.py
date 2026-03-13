from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from app.config import get_config
from app.errors import AppError
from app.poker.solver import SolverRecommendation, SolverSpotConfig
from app.services.solver_builder import render_texassolver_input
from app.services.solver_parser import parse_root_solver_recommendation

MOCK_SOLVER_OUTPUT = {
    "actions": ["CHECK", "BET 50", "BET 100"],
    "player": 1,
    "strategy": {
        "actions": ["CHECK", "BET 50", "BET 100"],
        "strategy": {
            "AsKd": [0.2, 0.65, 0.15],
            "KdAs": [0.2, 0.65, 0.15],
        },
    },
    "node_type": "action_node",
}


def _ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _solver_cache_paths(cache_key: str) -> tuple[Path, Path]:
    config = get_config()
    cache_dir = _ensure_directory(Path(config.solver_cache_dir))
    entry_dir = _ensure_directory(cache_dir / cache_key)
    return entry_dir / "spot.txt", entry_dir / "output_result.json"


def _mock_recommendation(spot: SolverSpotConfig) -> SolverRecommendation:
    return parse_root_solver_recommendation(
        MOCK_SOLVER_OUTPUT,
        spot,
        used_cached_result=False,
        mode="mock",
    )


async def solve_with_texassolver(spot: SolverSpotConfig) -> SolverRecommendation:
    config = get_config()
    spot_input_path, result_path = _solver_cache_paths(spot.cache_key())

    if result_path.exists():
        cached_output = json.loads(result_path.read_text())
        return parse_root_solver_recommendation(
            cached_output,
            spot,
            used_cached_result=True,
            mode="texassolver" if config.solver_mode == "texassolver" else "mock",
        )

    if config.solver_mode == "mock":
        output = MOCK_SOLVER_OUTPUT
        spot_input_path.write_text(render_texassolver_input(spot))
        result_path.write_text(json.dumps(output, indent=2))
        return _mock_recommendation(spot)

    solver_bin = Path(config.texassolver_bin or "")
    if not solver_bin.exists():
        raise AppError(
            "SOLVER_BINARY_MISSING",
            "TexasSolver binary was not found. Set TEXASSOLVER_BIN or switch SOLVER_MODE=mock.",
            details=str(solver_bin),
        )

    resource_dir = (
        Path(config.texassolver_resource_dir)
        if config.texassolver_resource_dir
        else solver_bin.parent / "resources"
    )
    if not resource_dir.exists():
        raise AppError(
            "SOLVER_RESOURCE_MISSING",
            "TexasSolver resources directory was not found.",
            details=str(resource_dir),
        )

    run_dir = _ensure_directory(Path(config.solver_work_dir) / spot.cache_key())
    input_path = run_dir / "spot.txt"
    output_path = run_dir / "output_result.json"
    input_path.write_text(render_texassolver_input(spot))

    command = [
        str(solver_bin),
        "-i",
        str(input_path),
        "-r",
        str(resource_dir),
        "-m",
        "holdem",
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=run_dir,
            capture_output=True,
            text=True,
            timeout=config.solver_timeout_ms / 1000,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AppError(
            "SOLVER_TIMEOUT",
            f"TexasSolver timed out after {config.solver_timeout_ms}ms.",
            status_code=504,
        ) from exc

    if completed.returncode != 0:
        raise AppError(
            "SOLVER_EXECUTION_ERROR",
            "TexasSolver returned a non-zero exit status.",
            details=completed.stderr.strip() or completed.stdout.strip(),
            status_code=502,
        )

    if not output_path.exists():
        raise AppError(
            "SOLVER_OUTPUT_MISSING",
            "TexasSolver completed without producing output_result.json.",
            details=completed.stdout.strip(),
            status_code=502,
        )

    shutil.copy2(input_path, spot_input_path)
    shutil.copy2(output_path, result_path)
    output = json.loads(output_path.read_text())
    return parse_root_solver_recommendation(
        output,
        spot,
        used_cached_result=False,
        mode="texassolver",
    )
