# AGENTS.md

This file is shared context for agents working in this repo. Read it before making changes, and update it whenever an important fact, decision, or constraint is learned.

## Repo Purpose
- This branch rewrites OpenFish mainly in Python.
- Current product goal: click one button, choose a browser monitor, tab, or window to capture, send the screenshot through a Python backend to a VLM endpoint, and render a structured plan suggestion back in the UI.
- GitHub repo identity remains `openfish` with the display title `🐟 OpenFish - Personal Ai Poker Assistant`.
- This repo is not yet a live poker-playing bot. The current release is still a visual planning assistant baseline.

## Current Stack
- `uv` for dependency management, locking, and tool execution.
- FastAPI for the application server and API routes.
- MCP Python SDK for exposing OpenFish as a tool server.
- Jinja2 templates plus lightweight browser JavaScript for the UI.
- Browser Media Capture APIs for screenshot collection.
- `pydantic` for runtime validation of requests and VLM responses.
- `pytest` for tests.

## Architecture Summary
- `app/main.py`: FastAPI entrypoint, page route, healthcheck, `/api/analyze`, and `/api/decide`.
- `app/cli.py`: Rich-powered local CLI that wraps the web app, MCP server, dummy VLM server, and doctor command.
- `app/mcp_server.py`: MCP entrypoint exposing the same OpenFish capabilities as MCP tools.
- `app/vlm_client.py`: OpenAI-compatible VLM client in Python.
- `app/parser.py`: strict JSON extraction and validation path for model output.
- `app/poker`: canonical poker-domain models for snapshots, events, state, profiles, and decision context.
- `app/poker/solver.py`: request/response models for solver-backed decisions.
- `app/agent/tools.py`: deterministic tool wrappers used by the decision layer.
- `app/services/event_diff.py`: turns sequential snapshots into ordered hand events.
- `app/services/state_reducer.py`: reduces events into canonical hand state.
- `app/services/context_builder.py`: builds model-ready temporal reasoning payloads.
- `app/services/solver_builder.py`: converts `HandState` into TexasSolver command input.
- `app/services/solver_parser.py`: parses root-node TexasSolver strategies for the hero combo.
- `app/services/texassolver_wrapper.py`: runs TexasSolver or mock mode and caches outputs.
- `app/services/decision_agent.py`: orchestrates tool use and returns a recommendation plus a tool trace.
- `app/testing/dummy_vlm_server.py`: OpenAI-compatible fake VLM server for testing.
- `app/testing/dummy_vlm_client.py`: helper client and CLI for driving dummy VLM scenarios.
- `app/static`: browser JavaScript and CSS.
- `app/templates`: server-rendered HTML shell.
- `prompts/system_prompts.md`: canonical example system prompts for OpenFish modes.
- Current capture implementation still uses `navigator.mediaDevices.getDisplayMedia()` in the browser, so the user must approve a browser picker and choose the screen, window, or tab to analyze.
- Monitor selection is only hintable from the app. The browser still owns the picker and the final display choice.

## How To Run
- Install and sync dependencies: `uv sync --dev`
- Open the CLI: `uv run --frozen openfish`
- Start the app: `uv run --frozen openfish ui`
- Start the MCP server: `uv run --frozen openfish mcp`
- Start the dummy VLM server: `uv run --frozen openfish dummy-vlm`
- Run config checks: `uv run --frozen openfish doctor`
- Open `http://127.0.0.1:8000`
- Run tests: `uv run --frozen pytest`
- Run formatters and checks:
  - `uv run --frozen ruff format .`
  - `uv run --frozen ruff check .`
  - `uv run --frozen pyright`
  - `uv run --frozen pre-commit run --all-files`

## Environment Variables
- `VLM_BASE_URL`
  - Default: `mock`
  - Use `mock` for a deterministic local baseline without network calls.
  - Use an OpenAI-compatible base URL for a live model, for example a local `vLLM` server.
- `VLM_API_KEY`
  - Optional in mock mode.
  - Sent as a bearer token when present.
- `VLM_MODEL`
  - Default: `gpt-4.1-mini`
- `VLM_TIMEOUT_MS`
  - Default: `20000`
- When testing with the dummy VLM server, point `VLM_BASE_URL` at `http://127.0.0.1:8010` and use a model/scenario such as `dummy-plan`.
- `SOLVER_MODE`
  - Default: `mock`
  - `mock` keeps the decision path testable without a local TexasSolver install.
  - `texassolver` runs the actual console solver.
- `TEXASSOLVER_BIN`
  - Path to the TexasSolver `console_solver` binary.
- `TEXASSOLVER_RESOURCE_DIR`
  - Path to the matching TexasSolver `resources` directory.
- `SOLVER_TIMEOUT_MS`
  - Default: `120000`
- `SOLVER_CACHE_DIR`
  - Default: `.openfish/solver-cache`
- `SOLVER_WORK_DIR`
  - Default: `.openfish/solver-runs`

## Current Workflow
1. Launch the browser UI with `uv run --frozen openfish ui`.
2. Click `Capture And Analyze`.
3. The browser opens a capture picker and the user selects a monitor, window, or tab.
4. The selected surface is captured as a PNG data URL in browser JavaScript.
5. The image is posted to the Python backend.
6. The backend calls the configured VLM endpoint with a fixed planning prompt.
7. The response is parsed as strict JSON and validated against the baseline schema.
8. The UI renders the screenshot preview, plan suggestion, and raw JSON debug output.

## Dummy VLM Workflow
1. Start `uv run --frozen openfish dummy-vlm`.
2. Set `VLM_BASE_URL=http://127.0.0.1:8010`.
3. Set `VLM_MODEL` to a scenario such as `dummy-plan` or `dummy-schema-error`.
4. Run the normal OpenFish analyze flow or call the helper client.

## Solver Workflow
1. Build or receive a canonical `HandState`.
2. Supply hero cards plus IP and OOP ranges.
3. Call `/api/decide`.
4. The decision agent runs tools to:
   - read the hand state
   - load opponent profiles
   - build decision context
   - compute pot odds
   - build a TexasSolver spot
   - run the solver tool
5. The endpoint returns a solver-backed recommendation and a `tool_trace`.

## MCP Workflow
1. Start `uv run --frozen openfish mcp`.
2. Connect an MCP client over `stdio` by default, or use `--transport sse` / `--transport streamable-http` if needed.
3. Call the OpenFish MCP tools instead of the HTTP routes when you want agent-native tool use.
4. Prefer:
   - `analyze_image` for screenshot planning
   - `build_decision_context` plus `compute_pot_odds` for grounded support data
   - `build_solver_spot` plus `solve_spot` for explicit TexasSolver-backed outputs
   - `decide_hand` for the full current orchestration path

## JSON Contract
```py
class PlanSuggestion(BaseModel):
    summary: str
    current_view: str
    goals: list[str]
    next_steps: list[str]
    risks: list[str]
    confidence: float
```

## Agent Working Rules
- Treat this file as canonical repo context for future agents.
- Update this file whenever an important fact is learned or a meaningful decision is made.
- Add short dated entries to the decision log instead of silently changing project assumptions.
- Prefer app-specific facts and current constraints over generic process notes.
- Keep commands accurate. If a script changes, update this file in the same change.
- Remove stale instructions instead of letting multiple conflicting notes accumulate.
- Use `uv` only for dependency management and tool execution. Do not use `pip`.
- After each major change, if the relevant checks pass, create a commit and push it before moving on.

## Roadmap
### Baseline
- Browser monitor, tab, or window screenshot capture
- Python-backed VLM analysis through an OpenAI-compatible endpoint
- Strict JSON validation in Python
- Screenshot preview, plan rendering, raw response debugging, and clear error states

### Expanded
- Session-oriented workflow with capture history, prompt presets, and response history
- Environment adapter boundary for different poker clients or target apps
- Support for region capture and richer browser automation paths
- Endpoint switching between mock, local, and remote OpenAI-compatible backends
- Saved transcripts and observations for debugging and future training data
- Later poker-specific interpretation schemas, after the visual analysis shell is stable
- Wire `TableSnapshot -> HandEvent -> HandState -> DecisionContext` into a live decision endpoint
- Add child-node traversal so solver recommendations can follow within-street betting history, not only the root node

## Decision Log
- 2026-03-12: Baseline app stack chosen as Electron + React + TypeScript + Vite.
- 2026-03-12: Baseline screenshot scope is the current app window only.
- 2026-03-12: VLM integration targets an OpenAI-compatible `/chat/completions` interface.
- 2026-03-12: Default local development mode uses `mock` mode so the app is usable without a live endpoint.
- 2026-03-12: Structured JSON output is the required baseline model contract; malformed output is treated as a first-class failure.
- 2026-03-12: Local macOS packaging currently succeeds with the default Electron icon and ad-hoc signing because no custom icon or notarization settings are configured yet.
- 2026-03-13: Dev startup must wait for both the Electron main bundle and preload bundle, otherwise the renderer can start without `window.electronAPI`.
- 2026-03-13: The baseline was converted from Electron to a browser-first Vite app that uses `getDisplayMedia()` instead of an Electron preload bridge.
- 2026-03-13: Live VLM calls now originate from the browser, so the target endpoint must permit cross-origin requests.
- 2026-03-13: A root `README.md` was added and the intended GitHub slug is `openfish`.
- 2026-03-13: The README title and project identity were updated to `🐟 OpenFish - Personal Ai Poker Assistant`.
- 2026-03-13: Browser capture now explicitly prefers monitor sharing and includes monitor surfaces in the picker, but web apps still cannot pre-select a specific display for the user.
- 2026-03-13: Branch `codex/python_dev` rewrites the app mainly in Python using FastAPI, while keeping browser capture in JavaScript because screen capture still requires client-side browser APIs.
- 2026-03-13: Example system prompts were added in `prompts/system_prompts.md` for planning, state extraction, coaching, and strict OCR-style observation.
- 2026-03-13: A temporal reasoning foundation was added under `app/poker` and `app/services` to support history-aware decision making across variable table sizes and stack depths.
- 2026-03-13: TexasSolver was integrated as a deterministic tool through a command-file wrapper, cached runs, root-node strategy parsing, and a new `/api/decide` endpoint.
- 2026-03-13: A dummy OpenAI-compatible VLM server/client pair was added for testing the analyze path and error scenarios without a real model endpoint.
- 2026-03-13: Live TexasSolver tests confirmed the current wrapper works end to end for real root-node OOP postflop spots; IP and child-node decisions remain unsupported until tree traversal is implemented.
- 2026-03-13: OpenFish now also exposes its core analyze/state/context/solver/decision capabilities through an MCP server via `app/mcp_server.py` and the `openfish-mcp` CLI entrypoint.
- 2026-03-13: The repo is now `uv`-first, tracks `uv.lock`, uses Ruff/Pyright/pre-commit for quality checks, and documents a restrictive source-available license in `LICENSE`.
- 2026-03-13: Future agents should commit and push after each major change once the relevant checks pass.
- 2026-03-13: OpenFish now has a Rich-based `openfish` CLI with a fish-themed welcome banner and subcommands for `ui`, `mcp`, `dummy-vlm`, and `doctor`.
