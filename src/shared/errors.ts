export type SerializedAppError = {
  code: string;
  message: string;
  details?: string;
  rawResponse?: string;
};

export function isSerializedAppError(
  value: unknown,
): value is SerializedAppError {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.code === 'string' && typeof candidate.message === 'string'
  );
}

export function normalizeError(error: unknown): SerializedAppError {
  if (isSerializedAppError(error)) {
    return error;
  }

  if (error instanceof Error) {
    return {
      code: 'UNKNOWN_ERROR',
      message: error.message,
    };
  }

  return {
    code: 'UNKNOWN_ERROR',
    message: 'An unknown error occurred.',
  };
}
