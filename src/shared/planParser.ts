import { planSuggestionSchema, type PlanSuggestion } from './contracts';

function extractJsonCandidate(raw: string): string {
  const fencedMatch = raw.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fencedMatch?.[1]) {
    return fencedMatch[1].trim();
  }

  const firstBrace = raw.indexOf('{');
  const lastBrace = raw.lastIndexOf('}');

  if (firstBrace === -1 || lastBrace === -1 || lastBrace <= firstBrace) {
    throw new Error('No JSON object found in the model response.');
  }

  return raw.slice(firstBrace, lastBrace + 1);
}

export function parsePlanSuggestion(raw: string): PlanSuggestion {
  const candidate = extractJsonCandidate(raw);
  const parsed = JSON.parse(candidate);
  return planSuggestionSchema.parse(parsed);
}
