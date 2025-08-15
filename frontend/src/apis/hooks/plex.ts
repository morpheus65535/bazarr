import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import {
  type PlexPinResponse,
  type PlexServer,
  type PlexServerConnection,
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckQuery,
  usePlexPinMutation,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
} from "@/apis/queries/plex";
import { PLEX_AUTH_CONFIG } from "@/constants/plex";

interface UsePlexOAuthOptions {
  onAuthSuccess?: (data: unknown) => void;
  onAuthError?: (error: unknown) => void;
}

export const usePlexOAuth = (options: UsePlexOAuthOptions = {}) => {
  const { onAuthSuccess, onAuthError } = options;
  const queryClient = useQueryClient();

  const [pinData, setPinData] = useState<PlexPinResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const pollingIntervalRef = useRef<number | null>(null);
  const pollingAttemptRef = useRef(0);
  const authWindowRef = useRef<Window | null>(null);

  const {
    data: authData,
    isLoading: authLoading,
    error: authError,
  } = usePlexAuthValidationQuery();

  const pinMutation = usePlexPinMutation();
  const logoutMutation = usePlexLogoutMutation();

  const { refetch: checkPin, error: pinCheckError } = usePlexPinCheckQuery(
    pinData?.pinId ?? null,
    !!pinData?.pinId,
  );

  const isAuthenticated = authData?.valid && authData?.auth_method === "oauth";
  const username = authData?.username;
  const email = authData?.email;
  const error = authError || pinCheckError;

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

  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      return;
    }

    setIsPolling(true);
    pollingAttemptRef.current = 0;

    pollingIntervalRef.current = window.setInterval(async () => {
      pollingAttemptRef.current++;

      if (pollingAttemptRef.current >= PLEX_AUTH_CONFIG.MAX_POLLING_ATTEMPTS) {
        cleanup();
        const timeoutError = new Error(
          "Authentication timeout. Please try again.",
        );

        if (onAuthError) {
          onAuthError(timeoutError);
        }

        return;
      }

      try {
        const result = await checkPin();

        if (result.data?.authenticated) {
          cleanup();
          // Invalidate auth queries to refresh the auth state
          queryClient.invalidateQueries({
            queryKey: [QueryKeys.Plex, "auth", "validate"],
          });

          if (onAuthSuccess) {
            onAuthSuccess(result.data);
          }
        }
      } catch (error) {
        // Continue polling on error unless it's a timeout
      }
    }, PLEX_AUTH_CONFIG.POLLING_INTERVAL_MS);
  }, [checkPin, cleanup, onAuthSuccess, onAuthError, queryClient]);

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

  const startAuth = useCallback(async () => {
    cleanup();

    const pin = await pinMutation.mutateAsync();
    setPinData(pin);

    authWindowRef.current = openAuthWindow(pin.authUrl);
    startPolling();

    return pin;
  }, [pinMutation, startPolling, cleanup, openAuthWindow]);

  const logout = useCallback(async () => {
    cleanup();
    await logoutMutation.mutateAsync();
  }, [logoutMutation, cleanup]);

  const cancelAuth = useCallback(() => {
    cleanup();
  }, [cleanup]);

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
    logout,
    cancelAuth,
  };
};

export const usePlexServers = () => {
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = authData?.valid && authData?.auth_method === "oauth";

  const getBestConnection = useCallback(
    (connections: PlexServerConnection[]): PlexServerConnection | null => {
      const availableConnections = connections.filter(
        (c) => c.available !== false,
      );
      if (availableConnections.length === 0) return null;

      return availableConnections.sort((a, b) => {
        if (a.local && !b.local) return -1;
        if (!a.local && b.local) return 1;
        return 0;
      })[0];
    },
    [],
  );

  const {
    data: servers = [],
    isLoading: serversLoading,
    error: serversError,
    refetch: refetchServers,
  } = usePlexServersQuery<PlexServer[]>({
    enabled: isAuthenticated,
    staleTime: 1000 * 30,
    select: (data) => {
      if (!data?.servers) return [];

      const serversWithBestConnections = data.servers.map(
        (server: PlexServer) => ({
          ...server,
          bestConnection: getBestConnection(server.connections),
        }),
      );

      // Sort servers with available connections first
      return serversWithBestConnections.sort((a: PlexServer, b: PlexServer) => {
        const aHasConnection = !!a.bestConnection;
        const bHasConnection = !!b.bestConnection;
        if (aHasConnection && !bHasConnection) return -1;
        if (!aHasConnection && bHasConnection) return 1;
        return 0;
      });
    },
  });

  const { data: selectedServer = null, isLoading: selectedServerLoading } =
    usePlexSelectedServerQuery<PlexServer | null>({
      enabled: isAuthenticated,
      select: (data) => data?.server || null,
    });

  const serverSelectionMutation = usePlexServerSelectionMutation();

  const selectServer = useCallback(
    async (machineIdentifier: string) => {
      const server = servers.find(
        (s: PlexServer) => s.machineIdentifier === machineIdentifier,
      );
      if (!server) {
        throw new Error(
          `Server with identifier '${machineIdentifier}' not found`,
        );
      }
      if (!server.bestConnection) {
        throw new Error(`Server '${server.name}' has no available connections`);
      }

      await serverSelectionMutation.mutateAsync({
        machineIdentifier,
        name: server.name,
        uri: server.bestConnection.uri,
        local: server.bestConnection.local,
      });
    },
    [servers, serverSelectionMutation],
  );

  return {
    servers,
    selectedServer,
    isLoading:
      serversLoading ||
      selectedServerLoading ||
      serverSelectionMutation.isPending,
    error: serversError?.message || undefined,
    refetchServers,
    selectServer,
  };
};
