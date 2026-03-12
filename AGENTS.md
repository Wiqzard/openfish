# AGENTS.md

This file is shared context for agents working in this repo. Read it before making changes, and update it whenever an important fact, decision, or constraint is learned.

## Repo Purpose
- Build a browser-based visual-agent interface for poker-related exploration, starting with a narrow baseline.
- Current product goal: click one button, choose a browser tab or window to capture, send the screenshot to a VLM endpoint, and render a structured plan suggestion back in the UI.
- Intended GitHub repo identity: `openfish` with the display title `🐟 OpenFish - Personal Ai Poker Assistant`.
- This repo is not yet a live poker-playing bot. The first release is a visual planning assistant.

## Current Stack
- React + Vite + TypeScript for the browser UI.
- Browser Media Capture APIs for screenshot collection.
- `zod` for runtime validation of VLM responses and captured image payloads.
- Vitest for unit tests.

## Architecture Summary
- `src/renderer`: React UI, browser capture flow, and VLM client logic.
- `src/shared`: shared contracts, parser logic, and error shapes.
- Current capture implementation uses `navigator.mediaDevices.getDisplayMedia()`, so the user must approve a browser picker and choose the tab or window to analyze.

## How To Run
- Install dependencies: `npm install`
- Start the app in dev mode: `npm run dev`
- Open the Vite dev URL shown in the terminal, usually `http://127.0.0.1:5173`
- Run tests: `npm test`
- Build production artifacts: `npm run build`
- Clean generated output manually if needed: `npm run clean`

## Environment Variables
- `VITE_VLM_BASE_URL`
  - Default: `mock`
  - Use `mock` for a deterministic local baseline without network calls.
  - Use an OpenAI-compatible base URL for a live model, for example a local `vLLM` server.
  - Because the request comes from the browser, the endpoint must allow CORS.
- `VITE_VLM_API_KEY`
  - Optional in mock mode.
  - Sent as a bearer token when present.
- `VITE_VLM_MODEL`
  - Default: `gpt-4.1-mini`
- `VITE_VLM_TIMEOUT_MS`
  - Default: `20000`

## Current Workflow
1. Launch the browser UI.
2. Click `Capture And Analyze`.
3. The browser opens a capture picker and the user selects a tab or window.
4. The selected surface is captured as a PNG data URL in the client.
5. The image is sent to the configured VLM endpoint with a fixed planning prompt.
6. The response is parsed as strict JSON and validated against the baseline schema.
7. The UI renders the screenshot preview, plan suggestion, and raw JSON debug output.

## JSON Contract
```ts
type PlanSuggestion = {
  summary: string
  current_view: string
  goals: string[]
  next_steps: string[]
  risks: string[]
  confidence: number
}
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
- Browser tab or window screenshot capture
- VLM analysis through an OpenAI-compatible endpoint
- Strict JSON validation
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
