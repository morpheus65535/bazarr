import { useCallback, useEffect, useRef, useState } from "react";
import { PLEX_AUTH_CONFIG, PLEX_ERROR_CODES } from "@/plex/constants/auth";
import {
  type PlexPinResponse,
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckMutation,
  usePlexPinMutation,
} from "@/plex/queries/plex";
import { parseAxiosError, type PlexError } from "@/plex/utilities/errors";

interface UsePlexOAuthOptions {
  onAuthSuccess?: (data: unknown) => void;
  onAuthError?: (error: PlexError) => void;
}

export const usePlexOAuth = (options: UsePlexOAuthOptions = {}) => {
  const { onAuthSuccess, onAuthError } = options;

  // Query for auth validation
  const {
    data: authData,
    isLoading: authLoading,
    error: authError,
    refetch: refetchAuth,
  } = usePlexAuthValidationQuery();

  // Mutations
  const pinMutation = usePlexPinMutation();
  const pinCheckMutation = usePlexPinCheckMutation();
  const logoutMutation = usePlexLogoutMutation();

  // Local state
  const [pinData, setPinData] = useState<PlexPinResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Refs for polling state
  const pollingIntervalRef = useRef<number | null>(null);
  const pollingAttemptRef = useRef(0);
  const authWindowRef = useRef<Window | null>(null);

  // Derived state from auth query
  const isAuthenticated = authData?.valid && authData?.auth_method === "oauth";
  const username = authData?.username;
  const email = authData?.email;
  const error = authError ? parseAxiosError(authError) : undefined;

  // Cleanup function
  const cleanup = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    pollingAttemptRef.current = 0;
    setIsPolling(false);

    if (authWindowRef.current && !authWindowRef.current.closed) {
      authWindowRef.current.close();
    }
    authWindowRef.current = null;

    setPinData(null);
  }, []);

  // Start polling for PIN check
  const startPolling = useCallback(
    (pinId: string) => {
      if (pollingIntervalRef.current) {
        return; // Already polling
      }

      setIsPolling(true);
      pollingAttemptRef.current = 0;

      pollingIntervalRef.current = window.setInterval(async () => {
        pollingAttemptRef.current++;

        // Check if we've exceeded max attempts
        if (
          pollingAttemptRef.current >= PLEX_AUTH_CONFIG.MAX_POLLING_ATTEMPTS
        ) {
          cleanup();
          const timeoutError: PlexError = {
            message: "Authentication timeout. Please try again.",
            code: PLEX_ERROR_CODES.AUTH_TIMEOUT,
          };

          if (onAuthError) {
            onAuthError(timeoutError);
          }

          return;
        }

        // Check PIN status
        try {
          const result = await pinCheckMutation.mutateAsync(pinId);

          if (result.authenticated) {
            cleanup();

            // Refetch auth validation to get fresh data
            await refetchAuth();

            if (onAuthSuccess) {
              onAuthSuccess(result);
            }
          }
        } catch (pinError) {
          const plexError = parseAxiosError(pinError);

          if (plexError.code === PLEX_ERROR_CODES.PIN_EXPIRED) {
            cleanup();
            if (onAuthError) {
              onAuthError(plexError);
            }
          }
          // Don't stop polling for other errors, just continue
        }
      }, PLEX_AUTH_CONFIG.POLLING_INTERVAL_MS);
    },
    [pinCheckMutation, cleanup, onAuthSuccess, onAuthError, refetchAuth],
  );

  // Open authentication window
  const openAuthWindow = useCallback((authUrl: string): Window | null => {
    const { width, height, features } = PLEX_AUTH_CONFIG.AUTH_WINDOW_CONFIG;
    const left = Math.round(window.screen.width / 2 - width / 2);
    const top = Math.round(window.screen.height / 2 - height / 2);

    return window.open(
      authUrl,
      "PlexAuth",
      `width=${width},height=${height},left=${left},top=${top},${features}`,
    );
  }, []);

  // Start authentication
  const startAuth = useCallback(async () => {
    try {
      cleanup(); // Clean up any existing state

      const pin = await pinMutation.mutateAsync();
      setPinData(pin);

      // Open auth window
      authWindowRef.current = openAuthWindow(pin.authUrl);

      // Start polling
      startPolling(pin.pinId);

      return pin;
    } catch (pinError) {
      const plexError = parseAxiosError(pinError);
      if (onAuthError) {
        onAuthError(plexError);
      }
      return null;
    }
  }, [pinMutation, startPolling, cleanup, openAuthWindow, onAuthError]);

  // Logout
  const logout = useCallback(async () => {
    try {
      cleanup();
      await logoutMutation.mutateAsync();
    } catch (logoutError) {
      const plexError = parseAxiosError(logoutError);
      if (onAuthError) {
        onAuthError(plexError);
      }
    }
  }, [logoutMutation, cleanup, onAuthError]);

  // Cancel authentication
  const cancelAuth = useCallback(() => {
    cleanup();
  }, [cleanup]);

  // Check auth status manually
  const checkAuthStatus = useCallback(() => {
    return refetchAuth();
  }, [refetchAuth]);

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return {
    isAuthenticated: !!isAuthenticated,
    isLoading: authLoading || pinMutation.isPending || logoutMutation.isPending,
    username,
    email,
    error,
    pinData,
    isPolling,
    startAuth,
    checkAuthStatus,
    logout,
    cancelAuth,
  };
};
