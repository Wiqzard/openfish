import { describe, expect, it } from 'vitest';

import { parsePlanSuggestion } from './planParser';

describe('parsePlanSuggestion', () => {
  it('parses raw JSON model output', () => {
    const result = parsePlanSuggestion(`
      {
        "summary": "Screenshot shows the baseline app home screen.",
        "current_view": "Home screen",
        "goals": ["Capture a screenshot"],
        "next_steps": ["Click the analyze button"],
        "risks": ["No VLM endpoint configured"],
        "confidence": 0.72
      }
    `);

    expect(result.summary).toContain('baseline app');
    expect(result.confidence).toBe(0.72);
  });

  it('parses fenced JSON responses', () => {
    const result = parsePlanSuggestion(`
      Here is the requested plan:
      \`\`\`json
      {
        "summary": "The app is ready for analysis.",
        "current_view": "Analysis screen",
        "goals": ["Inspect the screenshot"],
        "next_steps": ["Render the plan"],
        "risks": ["Malformed JSON"],
        "confidence": 0.61
      }
      \`\`\`
    `);

    expect(result.current_view).toBe('Analysis screen');
  });

  it('rejects invalid schema values', () => {
    expect(() =>
      parsePlanSuggestion(`
        {
          "summary": "Bad confidence value",
          "current_view": "Debug",
          "goals": ["Test"],
          "next_steps": ["Fix it"],
          "risks": ["Validation failure"],
          "confidence": 4
        }
      `),
    ).toThrow();
  });
});
