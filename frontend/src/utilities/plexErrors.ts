import { PLEX_ERROR_CODES, type PlexErrorCode } from "@/constants/plex";

interface AxiosErrorResponse {
  data?: {
    error?: string;
    code?: string;
  };
  status?: number;
}

interface AxiosError extends Error {
  response?: AxiosErrorResponse;
  isAxiosError?: boolean;
}

export interface PlexError {
  message: string;
  code: PlexErrorCode;
  isRetryable?: boolean;
}

export function createPlexError(
  message: string,
  code: PlexErrorCode,
  isRetryable = false,
): PlexError {
  return { message, code, isRetryable };
}

function isAxiosError(error: unknown): error is AxiosError {
  return typeof error === "object" && error !== null && "isAxiosError" in error;
}

function isError(error: unknown): error is Error {
  return error instanceof Error;
}

export function parseError(error: unknown): PlexError {
  if (isAxiosError(error)) {
    const responseData = error.response?.data;
    const errorCode = responseData?.code as PlexErrorCode;
    const errorMessage = responseData?.error || error.message;

    return createPlexError(
      errorMessage || "An unknown error occurred",
      errorCode || PLEX_ERROR_CODES.CONNECTION_ERROR,
      error.response?.status ? error.response.status >= 500 : false,
    );
  }

  if (isError(error)) {
    return createPlexError(error.message, PLEX_ERROR_CODES.CONNECTION_ERROR);
  }

  return createPlexError(
    "An unknown error occurred",
    PLEX_ERROR_CODES.CONNECTION_ERROR,
  );
}

export function getErrorMessage(error: PlexError): string {
  const codeMessages: Record<PlexErrorCode, string> = {
    [PLEX_ERROR_CODES.PIN_EXPIRED]:
      "Authentication PIN has expired. Please try again.",
    [PLEX_ERROR_CODES.AUTH_TIMEOUT]:
      "Authentication timed out. Please try again.",
    [PLEX_ERROR_CODES.CONNECTION_ERROR]:
      "Unable to connect to Plex. Please check your connection.",
    [PLEX_ERROR_CODES.INVALID_TOKEN]:
      "Invalid authentication token. Please re-authenticate.",
    [PLEX_ERROR_CODES.SERVER_NOT_FOUND]:
      "Plex server not found or unavailable.",
    [PLEX_ERROR_CODES.UNAUTHORIZED]:
      "Unauthorized access. Please re-authenticate.",
  };

  return (
    error.message || codeMessages[error.code] || "An unexpected error occurred"
  );
}
