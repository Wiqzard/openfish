# 🐟 OpenFish - Personal Ai Poker Assistant

OpenFish is a browser-based visual agent workspace for building a personal poker assistant. The current baseline focuses on a simple but useful first loop: capture a browser tab or window, send that image to a vision-language model, and turn the response into a structured next-step plan inside the UI.

## Overview

This project is aimed at poker environments that do not expose convenient APIs. Instead of starting with direct automation, OpenFish starts visually:

- capture a poker table or related interface
- analyze it with a VLM
- extract a structured plan
- keep the loop easy to inspect, debug, and improve

The current version is intentionally narrow. It is a foundation for a future personal AI poker assistant, not yet a live autonomous poker bot.

## Current Capabilities

- Browser-native capture flow for a selected tab or window
- Screenshot preview directly in the app
- OpenAI-compatible VLM request flow
- Strict JSON schema validation with `zod`
- Raw response debug panel for fast iteration
- Clear error handling for capture, network, timeout, and schema failures
- Mock mode for local development without a live model

## Product Direction

OpenFish is being built in stages.

### Stage 1: Visual Planning Baseline

- Capture a browser tab or window
- Send the screenshot to a VLM
- Receive a structured suggestion
- Render the result clearly in the UI

### Stage 2: Observation Workspace

- Capture history
- Saved sessions and transcripts
- Prompt presets
- Better visual debugging and replay

### Stage 3: Poker-Specific Intelligence

- Environment adapters for poker clients
- Richer observation schemas
- Table-state interpretation
- Later action planning and safer automation layers

## Tech Stack

- React
- Vite
- TypeScript
- Browser Media Capture APIs
- Zod
- Vitest

## Quick Start

### 1. Install dependencies

```bash
npm install
```

### 2. Start the app

```bash
npm run dev
```

Open the local Vite URL shown in the terminal, usually:

```bash
http://127.0.0.1:5173
```

### 3. Use the baseline flow

1. Click `Capture And Analyze`
2. Choose the browser tab or window to capture
3. Let OpenFish generate a structured plan suggestion
4. Review the screenshot preview, parsed plan, and raw JSON output

## Environment Configuration

Copy `.env.example` to `.env` and configure as needed:

```bash
VITE_VLM_BASE_URL=mock
VITE_VLM_API_KEY=
VITE_VLM_MODEL=gpt-4.1-mini
VITE_VLM_TIMEOUT_MS=20000
```

### Notes

- `mock` mode works without a live model.
- Live browser requests require the VLM endpoint to allow CORS.
- The app expects an OpenAI-compatible `/chat/completions` interface.

## Scripts

```bash
npm run dev
npm test
npm run build
npm run clean
```

## Response Contract

The current baseline expects the model to return strict JSON in this shape:

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

## Project Structure

```text
src/
  renderer/    Browser UI, capture flow, and VLM client
  shared/      Shared contracts, parser logic, and error shapes
```

## Why This Exists

Many poker tools and clients are visually rich but API-poor. OpenFish is designed to become a practical bridge between visual environments and agent workflows, starting with a minimal baseline that is easy to reason about and extend.

## Roadmap

- Improve capture workflows and saved sessions
- Add environment adapters for specific poker clients
- Expand from generic planning into poker-aware observation
- Add richer analysis and controlled action layers later
