import type { PlanSuggestion } from '../shared/contracts';
import { parsePlanSuggestion } from '../shared/planParser';

const SYSTEM_PROMPT = `You are a visual planning assistant for a browser screenshot.
Return exactly one JSON object and no surrounding commentary.

Required JSON schema:
{
  "summary": string,
  "current_view": string,
  "goals": string[],
  "next_steps": string[],
  "risks": string[],
  "confidence": number
}

Rules:
- Keep the response concise.
- confidence must be a number between 0 and 1.
- If something is unclear, mention it in risks instead of inventing certainty.
- Do not wrap the JSON in markdown fences.`;

const MOCK_PLAN: PlanSuggestion = {
  summary:
    'The screenshot shows the browser-based Poker VLM interface ready to analyze a selected tab or window.',
  current_view: 'Browser baseline home screen',
  goals: [
    'Capture the selected browser surface',
    'Send the image to the configured VLM endpoint',
  ],
  next_steps: [
    'Confirm the captured preview matches the intended tab or window',
    'Use the debug JSON panel to refine the prompt or downstream schema',
  ],
  risks: [
    'The browser capture picker requires manual user approval on each request',
    'Mock mode is enabled, so no live VLM call has been made yet',
  ],
  confidence: 0.51,
};

type AppConfig = {
  baseUrl: string;
  apiKey?: string;
  model: string;
  timeoutMs: number;
};

type ChatCompletionResponse = {
  choices?: Array<{
    message?: {
      content?:
        | string
        | Array<{
            text?: string;
            type?: string;
          }>;
    };
  }>;
};

function getAppConfig(): AppConfig {
  const timeout = Number.parseInt(import.meta.env.VITE_VLM_TIMEOUT_MS ?? '20000', 10);

  return {
    baseUrl: import.meta.env.VITE_VLM_BASE_URL?.trim() || 'mock',
    apiKey: import.meta.env.VITE_VLM_API_KEY?.trim() || undefined,
    model: import.meta.env.VITE_VLM_MODEL?.trim() || 'gpt-4.1-mini',
    timeoutMs: Number.isFinite(timeout) && timeout > 0 ? timeout : 20_000,
  };
}

function extractMessageText(response: ChatCompletionResponse): string {
  const content = response.choices?.[0]?.message?.content;

  if (typeof content === 'string' && content.trim().length > 0) {
    return content;
  }

  if (Array.isArray(content)) {
    const text = content
      .map((entry) => entry.text?.trim())
      .filter((entry): entry is string => Boolean(entry))
      .join('\n')
      .trim();

    if (text.length > 0) {
      return text;
    }
  }

  throw {
    code: 'VLM_EMPTY_RESPONSE',
    message: 'The VLM response did not contain any text content.',
  };
}

export async function requestPlanSuggestion(imageDataUrl: string): Promise<{
  plan: PlanSuggestion;
  rawResponse: string;
}> {
  const config = getAppConfig();

  if (config.baseUrl === 'mock') {
    return {
      plan: MOCK_PLAN,
      rawResponse: JSON.stringify(MOCK_PLAN, null, 2),
    };
  }

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), config.timeoutMs);

  try {
    const response = await fetch(
      `${config.baseUrl.replace(/\/$/, '')}/chat/completions`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(config.apiKey
            ? { Authorization: `Bearer ${config.apiKey}` }
            : {}),
        },
        body: JSON.stringify({
          model: config.model,
          temperature: 0,
          messages: [
            {
              role: 'system',
              content: SYSTEM_PROMPT,
            },
            {
              role: 'user',
              content: [
                {
                  type: 'text',
                  text:
                    'Analyze this browser screenshot and return the requested JSON plan. Focus on what the user should do next.',
                },
                {
                  type: 'image_url',
                  image_url: {
                    url: imageDataUrl,
                  },
                },
              ],
            },
          ],
        }),
        signal: controller.signal,
      },
    );

    const responseText = await response.text();

    if (!response.ok) {
      throw {
        code: 'VLM_HTTP_ERROR',
        message: `The VLM request failed with ${response.status} ${response.statusText}.`,
        rawResponse: responseText,
      };
    }

    let parsedResponse: ChatCompletionResponse;
    try {
      parsedResponse = JSON.parse(responseText) as ChatCompletionResponse;
    } catch {
      throw {
        code: 'VLM_BAD_JSON',
        message: 'The VLM returned invalid JSON.',
        rawResponse: responseText,
      };
    }

    const rawResponse = extractMessageText(parsedResponse);

    try {
      return {
        plan: parsePlanSuggestion(rawResponse),
        rawResponse,
      };
    } catch (error) {
      throw {
        code: 'VLM_SCHEMA_ERROR',
        message: 'The VLM response did not match the expected plan schema.',
        details: error instanceof Error ? error.message : undefined,
        rawResponse,
      };
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw {
        code: 'VLM_TIMEOUT',
        message: `The VLM request timed out after ${config.timeoutMs}ms.`,
      };
    }

    if (error instanceof TypeError) {
      throw {
        code: 'VLM_NETWORK_ERROR',
        message:
          'The browser could not reach the VLM endpoint. Check the URL, make sure the server is running, and verify CORS is enabled for browser requests.',
      };
    }

    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}
