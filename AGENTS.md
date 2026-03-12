# AGENTS.md

This file is shared context for agents working in this repo. Read it before making changes, and update it whenever an important fact, decision, or constraint is learned.

## Repo Purpose
- This branch rewrites OpenFish mainly in Python.
- Current product goal: click one button, choose a browser monitor, tab, or window to capture, send the screenshot through a Python backend to a VLM endpoint, and render a structured plan suggestion back in the UI.
- GitHub repo identity remains `openfish` with the display title `🐟 OpenFish - Personal Ai Poker Assistant`.
- This repo is not yet a live poker-playing bot. The current release is still a visual planning assistant baseline.

## Current Stack
- FastAPI for the application server and API routes.
- Jinja2 templates plus lightweight browser JavaScript for the UI.
- Browser Media Capture APIs for screenshot collection.
- `pydantic` for runtime validation of requests and VLM responses.
- `pytest` for tests.

## Architecture Summary
- `app/main.py`: FastAPI entrypoint, page route, healthcheck, and `/api/analyze`.
- `app/vlm_client.py`: OpenAI-compatible VLM client in Python.
- `app/parser.py`: strict JSON extraction and validation path for model output.
- `app/static`: browser JavaScript and CSS.
- `app/templates`: server-rendered HTML shell.
- Current capture implementation still uses `navigator.mediaDevices.getDisplayMedia()` in the browser, so the user must approve a browser picker and choose the screen, window, or tab to analyze.
- Monitor selection is only hintable from the app. The browser still owns the picker and the final display choice.

## How To Run
- Create and activate a virtual environment:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
- Install dependencies: `pip install -e ".[dev]"`
- Start the app: `uvicorn app.main:app --reload`
- Open `http://127.0.0.1:8000`
- Run tests: `pytest`

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

## Current Workflow
1. Launch the browser UI.
2. Click `Capture And Analyze`.
3. The browser opens a capture picker and the user selects a monitor, window, or tab.
4. The selected surface is captured as a PNG data URL in browser JavaScript.
5. The image is posted to the Python backend.
6. The backend calls the configured VLM endpoint with a fixed planning prompt.
7. The response is parsed as strict JSON and validated against the baseline schema.
8. The UI renders the screenshot preview, plan suggestion, and raw JSON debug output.

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
