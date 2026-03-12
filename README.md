# 🐟 OpenFish - Personal Ai Poker Assistant

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
- VLM request handling moved into Python with `httpx`
- JSON schema validation moved into Python with `pydantic`
- Tests now run with `pytest`

## Tech Stack

- Python 3.12+
- FastAPI
- Jinja2
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

## Environment Configuration

Copy `.env.example` to `.env` and set values as needed:

```bash
VLM_BASE_URL=mock
VLM_API_KEY=
VLM_MODEL=gpt-4.1-mini
VLM_TIMEOUT_MS=20000
```

### Notes

- `mock` mode works without a live model.
- The backend expects an OpenAI-compatible `/chat/completions` interface.
- Because the VLM request is now server-side, you no longer need CORS for local development in this branch.
- To capture a specific monitor, choose `Entire Screen` in the browser picker and then select the display you want.

## Current Capabilities

- Browser-native capture flow for a selected monitor, window, or tab
- Python-backed `/api/analyze` endpoint
- Screenshot preview directly in the app
- Structured plan rendering
- Raw response debug panel
- Clear error handling for capture, network, timeout, and schema failures
- Mock mode for local development

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

## Project Structure

```text
app/
  main.py           FastAPI entrypoint and routes
  config.py         Environment-backed settings
  errors.py         App-level error shape
  models.py         Pydantic request and response models
  parser.py         JSON extraction and plan parsing
  vlm_client.py     OpenAI-compatible VLM client
  static/           Browser JS and CSS
  templates/        Server-rendered HTML
tests/
  test_api.py
  test_parser.py
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
