# 🐟 OpenFish - Personal AI Poker Assistant

This branch rewrites OpenFish mainly in Python.

OpenFish is a browser-based visual agent workspace for building a personal poker assistant in API-poor poker environments. The current baseline focuses on a tight first loop:

1. Capture a browser tab, window, or monitor
2. Send the screenshot through a Python backend to a VLM
3. Parse a strict JSON response
4. Render a clear plan in the UI

The browser still handles screen capture because web capture APIs must run client-side, but the application flow, prompt orchestration, validation, and VLM integration now live mainly in Python.

## What Changed On `codex/python_dev`

- React/Vite frontend replaced with a lightweight static browser UI
- FastAPI now serves the app and owns the `/api/analyze` workflow
- FastAPI now also serves `/api/decide` for solver-backed decisions
- VLM request handling moved into Python with `httpx`
- JSON schema validation moved into Python with `pydantic`
- Tests now run with `pytest`

## Tech Stack

- Python 3.12+
- FastAPI
- Jinja2
- MCP Python SDK
- Pydantic
- HTTPX
- Browser Media Capture APIs
- Pytest

## Quick Start

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -e ".[dev]"
```

### 3. Start the server

```bash
uvicorn app.main:app --reload
```

Then open:

```bash
http://127.0.0.1:8000
```

### 4. Start the MCP server

```bash
openfish-mcp
```

This runs OpenFish as an MCP tool server over `stdio`.

Optional transports:

```bash
openfish-mcp --transport sse
openfish-mcp --transport streamable-http
```

## Environment Configuration

Copy `.env.example` to `.env` and set values as needed:

```bash
VLM_BASE_URL=mock
VLM_API_KEY=
VLM_MODEL=gpt-4.1-mini
VLM_TIMEOUT_MS=20000
SOLVER_MODE=mock
TEXASSOLVER_BIN=
TEXASSOLVER_RESOURCE_DIR=
SOLVER_TIMEOUT_MS=120000
SOLVER_CACHE_DIR=.openfish/solver-cache
SOLVER_WORK_DIR=.openfish/solver-runs
```

### Notes

- `mock` mode works without a live model.
- The backend expects an OpenAI-compatible `/chat/completions` interface.
- Because the VLM request is now server-side, you no longer need CORS for local development in this branch.
- To capture a specific monitor, choose `Entire Screen` in the browser picker and then select the display you want.
- `SOLVER_MODE=mock` keeps the solver tool testable without a local TexasSolver install.
- For live TexasSolver runs, point `TEXASSOLVER_BIN` at `console_solver` and `TEXASSOLVER_RESOURCE_DIR` at the matching `resources` directory from the TexasSolver release package.

## Current Capabilities

- Browser-native capture flow for a selected monitor, window, or tab
- Python-backed `/api/analyze` endpoint
- Python-backed `/api/decide` endpoint with tool-style solver orchestration
- MCP server exposing the same analysis and decision capabilities as tools
- Screenshot preview directly in the app
- Structured plan rendering
- Raw response debug panel
- Clear error handling for capture, network, timeout, and schema failures
- Mock mode for local development
- Event-sourced poker reasoning foundation with snapshots, events, hand state, opponent profiles, and decision-context building
- TexasSolver integration path with cacheable spot generation and root-node action recommendations

## Prompt Examples

Example system prompts live in [prompts/system_prompts.md](/Users/sebastianstapf/Documents/projects/Poker/prompts/system_prompts.md).

Included prompt variants:

- General visual planning
- Poker table state extraction
- Poker coach / strategy advisor
- Strict OCR-style observation

## Dummy VLM Test Harness

This branch now includes a dummy OpenAI-compatible VLM server and client for testing.

Files:

- [dummy_vlm_server.py](/Users/sebastianstapf/Documents/projects/Poker/app/testing/dummy_vlm_server.py)
- [dummy_vlm_client.py](/Users/sebastianstapf/Documents/projects/Poker/app/testing/dummy_vlm_client.py)

Run the fake server:

```bash
openfish-dummy-vlm
```

Or:

```bash
python -m app.testing.dummy_vlm_server
```

Call it from the helper client:

```bash
openfish-dummy-vlm-client --scenario dummy-plan
openfish-dummy-vlm-client --scenario dummy-schema-error
openfish-dummy-vlm-client --scenario dummy-http-error
```

Supported scenarios:

- `dummy-plan`
- `dummy-text-array`
- `dummy-schema-error`
- `dummy-http-error`
- `dummy-bad-json-body`
- `dummy-delay`

To point OpenFish at the dummy server:

```bash
VLM_BASE_URL=http://127.0.0.1:8010
VLM_MODEL=dummy-plan
```

## API Contract

### Request

```json
{
  "image": {
    "dataUrl": "data:image/png;base64,...",
    "width": 1440,
    "height": 900,
    "surfaceType": "monitor"
  }
}
```

### Response

```json
{
  "image": {
    "dataUrl": "data:image/png;base64,...",
    "width": 1440,
    "height": 900,
    "surfaceType": "monitor"
  },
  "plan": {
    "summary": "string",
    "current_view": "string",
    "goals": ["string"],
    "next_steps": ["string"],
    "risks": ["string"],
    "confidence": 0.65
  },
  "rawResponse": "{...}"
}
```

## Decision Endpoint

`POST /api/decide` accepts:

- a canonical `HandState`
- hero hole cards
- hero position (`ip` or `oop`)
- IP and OOP ranges
- optional opponent profiles

The endpoint then:

1. reads the current hand state
2. builds a compact decision context
3. computes pot odds
4. builds a TexasSolver command-file spot
5. runs the solver tool in mock or live mode
6. returns a recommendation plus a tool trace

## MCP Server

OpenFish can now run as an MCP server so external agents can use the repo as a tool provider.

Run it with:

```bash
openfish-mcp
```

Current MCP tools:

- `analyze_image`
- `get_current_hand_state`
- `get_opponent_profiles`
- `compute_pot_odds`
- `build_decision_context`
- `build_solver_spot`
- `solve_spot`
- `decide_hand`

Recommended usage:

1. Use `analyze_image` for screenshot-to-plan testing.
2. Use `build_decision_context` and `compute_pot_odds` for grounded reasoning support.
3. Use `build_solver_spot` and `solve_spot` when you want explicit TexasSolver-backed outputs.
4. Use `decide_hand` when you want the full current OpenFish tool chain in one call.

Current solver limitation:

- The MCP solver path still only supports root-node postflop spots where hero is `OOP`.
- IP decisions and child-node traversal remain future work.

## Project Structure

```text
app/
  agent/           Tool-style decision orchestration
  main.py           FastAPI entrypoint and routes
  mcp_server.py     MCP server exposing OpenFish tools
  config.py         Environment-backed settings
  errors.py         App-level error shape
  models.py         Pydantic request and response models
  poker/            Snapshot, event, state, profile, and context models
  parser.py         JSON extraction and plan parsing
  services/         Event diffing, state reduction, decision and solver services
  vlm_client.py     OpenAI-compatible VLM client
  static/           Browser JS and CSS
  templates/        Server-rendered HTML
tests/
  test_api.py
  test_decision_agent.py
  test_dummy_vlm.py
  test_mcp_server.py
  test_parser.py
  test_poker_reasoning.py
```

## Running Tests

```bash
pytest
```

## Why This Branch Exists

This branch is the Python-first version of OpenFish. It is useful if you want:

- backend-controlled VLM integrations
- Python-native validation and orchestration
- an easier path toward Python-based poker reasoning or simulation
- less frontend framework overhead in the baseline

## Temporal Reasoning Foundation

The branch now includes the base objects needed for reasoning over time:

- `TableSnapshot` for one observed frame
- `HandEvent` for ordered changes extracted from snapshots
- `HandState` for canonical current hand truth
- `OpponentProfile` for long-term player memory
- `DecisionContext` for model-ready prompt input

The intended pipeline is:

1. Parse a screenshot into a `TableSnapshot`
2. Diff it against the previous snapshot into `HandEvent`s
3. Reduce events into `HandState`
4. Merge relevant `OpponentProfile` summaries
5. Build a compact `DecisionContext` for the reasoning model

## Test Utilities

The dummy VLM server is useful for validating:

- the `/api/analyze` path against OpenAI-compatible responses
- text-array style assistant content
- schema-validation failures
- HTTP failures
- delayed responses and timeout handling

## TexasSolver Tool Integration

OpenFish now treats TexasSolver as a deterministic expert tool rather than the agent itself.

The current integration:

- builds a TexasSolver command file from the observed hand state
- caches solves by a stable spot hash
- runs the console solver in live mode or a mock solver in development
- parses the root-node strategy for the hero combo
- returns the best-frequency action with a tool trace

Current limitation:

- the first implementation solves the root node for the provided street
- it does not yet traverse down the TexasSolver child tree for within-street action sequences
- so it is best suited to OOP street-entry decisions until node-path mapping is added
