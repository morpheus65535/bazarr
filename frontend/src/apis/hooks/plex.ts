import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  type PlexPinResponse,
  type PlexServer,
  type PlexServerConnection,
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckMutation,
  usePlexPinMutation,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
} from "@/apis/queries/plex";
import { PLEX_AUTH_CONFIG, PLEX_ERROR_CODES } from "@/constants/plex";
import { parseError, type PlexError } from "@/utilities/plexErrors";

interface UsePlexOAuthOptions {
  onAuthSuccess?: (data: unknown) => void;
  onAuthError?: (error: PlexError) => void;
}

export const usePlexOAuth = (options: UsePlexOAuthOptions = {}) => {
  const { onAuthSuccess, onAuthError } = options;

  const {
    data: authData,
    isLoading: authLoading,
    error: authError,
    refetch: refetchAuth,
  } = usePlexAuthValidationQuery();

  const pinMutation = usePlexPinMutation();
  const pinCheckMutation = usePlexPinCheckMutation();
  const logoutMutation = usePlexLogoutMutation();

  const [pinData, setPinData] = useState<PlexPinResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const pollingIntervalRef = useRef<number | null>(null);
  const pollingAttemptRef = useRef(0);
  const authWindowRef = useRef<Window | null>(null);

  const isAuthenticated = authData?.valid && authData?.auth_method === "oauth";
  const username = authData?.username;
  const email = authData?.email;
  const error = authError ? parseError(authError) : undefined;

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

  const startPolling = useCallback(
    (pinId: string) => {
      if (pollingIntervalRef.current) {
        return;
      }

      setIsPolling(true);
      pollingAttemptRef.current = 0;

      pollingIntervalRef.current = window.setInterval(async () => {
        pollingAttemptRef.current++;

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

        const result = await pinCheckMutation.mutateAsync(pinId);

        if (result.authenticated) {
          cleanup();
          await refetchAuth();

          if (onAuthSuccess) {
            onAuthSuccess(result);
          }
        }
      }, PLEX_AUTH_CONFIG.POLLING_INTERVAL_MS);
    },
    [pinCheckMutation, cleanup, onAuthSuccess, onAuthError, refetchAuth],
  );

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
    startPolling(pin.pinId);

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
  const {
    data: serversResponse,
    isLoading: serversLoading,
    error: serversError,
    refetch: refetchServers,
  } = usePlexServersQuery();

  const {
    data: selectedServerResponse,
    isLoading: selectedServerLoading,
    refetch: refetchSelectedServer,
  } = usePlexSelectedServerQuery();

  const serverSelectionMutation = usePlexServerSelectionMutation();

  const [processedServers, setProcessedServers] = useState<PlexServer[]>([]);
  const [lastFetch, setLastFetch] = useState<number | undefined>();
  const [cachedSelectedServer, setCachedSelectedServer] =
    useState<PlexServer | null>(null);

  const rawServers: PlexServer[] = useMemo(
    () => serversResponse?.servers || [],
    [serversResponse?.servers],
  );
  const selectedServer = selectedServerResponse?.server || null;

  const servers = processedServers.length > 0 ? processedServers : rawServers;

  useEffect(() => {
    if (rawServers.length === 0) {
      setProcessedServers([]);
    }
  }, [rawServers]);

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

  const shouldThrottleFetch = useCallback(
    (throttleMs: number = 30000): boolean => {
      const now = Date.now();
      return !!(lastFetch && now - lastFetch < throttleMs);
    },
    [lastFetch],
  );

  const fetchServers = useCallback(async () => {
    if (shouldThrottleFetch()) {
      return servers;
    }
    setLastFetch(Date.now());
    const response = await refetchServers();
    if (response.data?.servers) {
      const serversWithBestConnections = response.data.servers.map(
        (server: PlexServer) => {
          return {
            ...server,
            bestConnection: getBestConnection(server.connections),
          };
        },
      );

      serversWithBestConnections.sort((a: PlexServer, b: PlexServer) => {
        const aHasConnection = !!a.bestConnection;
        const bHasConnection = !!b.bestConnection;
        if (aHasConnection && !bHasConnection) return -1;
        if (!aHasConnection && bHasConnection) return 1;
        return 0;
      });
      setProcessedServers(serversWithBestConnections);
      return serversWithBestConnections;
    }
    return [];
  }, [servers, refetchServers, getBestConnection, shouldThrottleFetch]);

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
      setCachedSelectedServer(server);
    },
    [servers, serverSelectionMutation, setCachedSelectedServer],
  );

  const getSelectedServer = useCallback(async () => {
    const response = await refetchSelectedServer();
    return response.data?.server || null;
  }, [refetchSelectedServer]);

  return {
    servers,
    selectedServer,
    cachedSelectedServer,
    isLoading:
      serversLoading ||
      selectedServerLoading ||
      serverSelectionMutation.isPending,
    error: serversError?.message || undefined,
    fetchServers,
    refreshServers: fetchServers,
    selectServer,
    getSelectedServer,
  };
};

export const useServerSelection = () => {
  const [selectedServerId, setSelectedServerId] = useState("");
  const [isSelecting, setSelecting] = useState(false);
  const [isSaved, setSaved] = useState(false);
  const [selectedServer, setSelectedServer] = useState<PlexServer | null>(null);

  const reset = useCallback(() => {
    setSelectedServerId("");
    setSelecting(false);
    setSaved(false);
    setSelectedServer(null);
  }, []);

  const updateSelectedServer = useCallback((server: PlexServer | null) => {
    setSelectedServer(server);
    setSelectedServerId(server?.machineIdentifier || "");
  }, []);

  return {
    selectedServerId,
    isSelecting,
    isSaved,
    selectedServer,
    setSelectedServerId,
    setSelecting,
    setSaved,
    setSelectedServer: updateSelectedServer,
    reset,
  };
};
