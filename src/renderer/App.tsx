import { useMemo, useState } from 'react';

import type {
  AnalysisResult,
  CapturedImage,
  PlanSuggestion,
} from '../shared/contracts';
import { normalizeError, type SerializedAppError } from '../shared/errors';
import { captureBrowserSurface } from './browserCapture';
import { requestPlanSuggestion } from './vlmClient';

function formatConfidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

function ListSection({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  return (
    <section className="card">
      <h3>{title}</h3>
      <ul className="bullet-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function ScreenshotPreview({ image }: { image: CapturedImage }) {
  return (
    <section className="card preview-card">
      <div className="section-heading">
        <h3>Screenshot Preview</h3>
        <span>
          {image.surfaceType === 'monitor'
            ? 'Monitor'
            : image.surfaceType === 'window'
              ? 'Window'
              : image.surfaceType === 'browser'
                ? 'Tab'
                : 'Unknown source'}
          {' '}
          ·
          {' '}
          {image.width} x {image.height}
        </span>
      </div>
      <img
        className="preview-image"
        src={image.dataUrl}
        alt="Captured browser screenshot"
      />
    </section>
  );
}

function PlanPanel({ plan }: { plan: PlanSuggestion }) {
  return (
    <div className="plan-grid">
      <section className="card plan-summary">
        <div className="section-heading">
          <h3>Plan Suggestion</h3>
          <span className="confidence-pill">
            Confidence {formatConfidence(plan.confidence)}
          </span>
        </div>
        <p className="summary-text">{plan.summary}</p>
        <p className="current-view">
          Current view:
          {' '}
          <strong>{plan.current_view}</strong>
        </p>
      </section>
      <ListSection title="Goals" items={plan.goals} />
      <ListSection title="Next Steps" items={plan.next_steps} />
      <ListSection title="Risks" items={plan.risks} />
    </div>
  );
}

function ErrorPanel({ error }: { error: SerializedAppError }) {
  return (
    <section className="card error-card">
      <div className="section-heading">
        <h3>Error</h3>
        <span>{error.code}</span>
      </div>
      <p>{error.message}</p>
      {error.details ? <p className="error-detail">{error.details}</p> : null}
      {error.rawResponse ? (
        <pre className="debug-panel">{error.rawResponse}</pre>
      ) : null}
    </section>
  );
}

export function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<SerializedAppError | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const debugJson = useMemo(() => {
    if (!result) {
      return '';
    }

    return result.rawResponse;
  }, [result]);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const image = await captureBrowserSurface();
      const { plan, rawResponse } = await requestPlanSuggestion(image.dataUrl);
      const nextResult: AnalysisResult = {
        image,
        plan,
        rawResponse,
      };
      setResult(nextResult);
    } catch (caughtError) {
      setError(normalizeError(caughtError));
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <section className="hero card">
        <div>
          <p className="eyebrow">Poker VLM Baseline</p>
          <h1>Browser screenshot analysis for the first agent loop</h1>
          <p className="hero-copy">
            Click once to open the browser capture picker, choose the monitor,
            window, or tab you want to analyze, send that screenshot to an
            OpenAI-compatible VLM endpoint, and render a structured plan
            suggestion back in the UI.
          </p>
        </div>
        <div className="hero-actions">
          <button
            className="primary-button"
            onClick={handleAnalyze}
            disabled={isLoading}
            type="button"
          >
            {isLoading ? 'Capturing And Analyzing...' : 'Capture And Analyze'}
          </button>
          <p className="hint-text">
            The browser will ask you to choose a source. To capture a specific
            monitor, select <code>Entire Screen</code> in the picker and then
            choose the display you want. Default endpoint mode is <code>mock</code>.
            Set the VLM environment variables to switch to a live model.
          </p>
        </div>
      </section>

      {error ? <ErrorPanel error={error} /> : null}

      {result ? (
        <section className="content-grid">
          <ScreenshotPreview image={result.image} />
          <div className="results-column">
            <PlanPanel plan={result.plan} />
            <section className="card">
              <div className="section-heading">
                <h3>Raw JSON Debug</h3>
                <span>Model output</span>
              </div>
              <pre className="debug-panel">{debugJson}</pre>
            </section>
          </div>
        </section>
      ) : (
        <section className="empty-state card">
          <h2>No screenshot analyzed yet</h2>
          <p>
            The first milestone is intentionally narrow: use browser-native
            capture, keep the model call and schema validation obvious, and make
            the UI easy to debug before expanding toward richer visual-agent
            behavior. Monitor selection happens in the browser picker itself.
          </p>
        </section>
      )}
    </main>
  );
}
