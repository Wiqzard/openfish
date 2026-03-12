import { z } from 'zod';

export const capturedImageSchema = z.object({
  dataUrl: z.string().startsWith('data:image/png;base64,'),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
});

export const planSuggestionSchema = z.object({
  summary: z.string().min(1),
  current_view: z.string().min(1),
  goals: z.array(z.string().min(1)),
  next_steps: z.array(z.string().min(1)),
  risks: z.array(z.string().min(1)),
  confidence: z.number().min(0).max(1),
});

export const analysisResultSchema = z.object({
  image: capturedImageSchema,
  plan: planSuggestionSchema,
  rawResponse: z.string().min(1),
});

export type CapturedImage = z.infer<typeof capturedImageSchema>;
export type PlanSuggestion = z.infer<typeof planSuggestionSchema>;
export type AnalysisResult = z.infer<typeof analysisResultSchema>;
