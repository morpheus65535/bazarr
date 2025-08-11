import { PLEX_ERROR_CODES, type PlexErrorCode } from "@/plex/constants/auth";

export interface PlexError {
  message: string;
  code: PlexErrorCode;
  isRetryable?: boolean;
}

interface AxiosError extends Error {
  response?: {
    data?: { error?: string; code?: string };
    status?: number;
  };
  isAxiosError?: boolean;
}

export function parseAxiosError(error: unknown): PlexError {
  // Handle axios errors
  if (error && typeof error === "object" && "isAxiosError" in error) {
    const axiosError = error as AxiosError;
    const responseData = axiosError.response?.data;
    const errorCode =
      (responseData?.code as PlexErrorCode) ||
      PLEX_ERROR_CODES.CONNECTION_ERROR;
    const message =
      responseData?.error || axiosError.message || "Connection error";
    const isRetryable = axiosError.response?.status
      ? axiosError.response.status >= 500
      : false;

    return { message, code: errorCode, isRetryable };
  }

  // Handle generic errors
  if (error instanceof Error) {
    return {
      message: error.message,
      code: PLEX_ERROR_CODES.CONNECTION_ERROR,
      isRetryable: false,
    };
  }

  // Fallback
  return {
    message: "An unknown error occurred",
    code: PLEX_ERROR_CODES.CONNECTION_ERROR,
    isRetryable: false,
  };
}

export function getErrorMessage(error: PlexError): string {
  const messages: Record<PlexErrorCode, string> = {
    [PLEX_ERROR_CODES.PIN_EXPIRED]:
      "Authentication PIN expired. Please try again.",
    [PLEX_ERROR_CODES.AUTH_TIMEOUT]:
      "Authentication timed out. Please try again.",
    [PLEX_ERROR_CODES.CONNECTION_ERROR]: "Unable to connect to Plex.",
    [PLEX_ERROR_CODES.INVALID_TOKEN]: "Invalid token. Please re-authenticate.",
    [PLEX_ERROR_CODES.SERVER_NOT_FOUND]: "Plex server not found.",
    [PLEX_ERROR_CODES.UNAUTHORIZED]: "Unauthorized. Please re-authenticate.",
  };

  return (
    error.message || messages[error.code] || "An unexpected error occurred"
  );
}
