export const PLEX_AUTH_CONFIG = {
  POLLING_INTERVAL_MS: 2000,
  MAX_POLLING_ATTEMPTS: 150,
  AUTH_WINDOW_CONFIG: {
    width: 600,
    height: 700,
    features:
      "menubar=no,toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes",
  },
} as const;

export const PLEX_ERROR_CODES = {
  PIN_EXPIRED: "PIN_EXPIRED",
  AUTH_TIMEOUT: "AUTH_TIMEOUT",
  CONNECTION_ERROR: "CONNECTION_ERROR",
  INVALID_TOKEN: "INVALID_TOKEN",
  SERVER_NOT_FOUND: "SERVER_NOT_FOUND",
  UNAUTHORIZED: "UNAUTHORIZED",
} as const;

export type PlexErrorCode =
  (typeof PLEX_ERROR_CODES)[keyof typeof PLEX_ERROR_CODES];
