import {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from "react";
import { PLEX_AUTH_CONFIG, PLEX_ERROR_CODES } from "@/plex/constants/auth";
import {
  type PlexPinResponse,
  type PlexServer,
  type PlexServerConnection,
  usePlexAuthValidationQuery,
  usePlexConnectionTestMutation,
  usePlexLogoutMutation,
  usePlexPinCheckMutation,
  usePlexPinMutation,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
} from "@/plex/queries/plex";
import { parseAxiosError, type PlexError } from "@/plex/utilities/errors";

// Server Selection State Management
interface ServerSelectionState {
  selectedServerId: string;
  isSelecting: boolean;
  isSaved: boolean;
  selectedServer: PlexServer | null;
}

type ServerSelectionAction =
  | { type: "SET_SELECTED_SERVER_ID"; payload: string }
  | { type: "SET_SELECTING"; payload: boolean }
  | { type: "SET_SAVED"; payload: boolean }
  | { type: "SET_SELECTED_SERVER"; payload: PlexServer | null }
  | { type: "RESET" };

const initialSelectionState: ServerSelectionState = {
  selectedServerId: "",
  isSelecting: false,
  isSaved: false,
  selectedServer: null,
};

function serverSelectionReducer(
  state: ServerSelectionState,
  action: ServerSelectionAction,
): ServerSelectionState {
  switch (action.type) {
    case "SET_SELECTED_SERVER_ID":
      return { ...state, selectedServerId: action.payload };
    case "SET_SELECTING":
      return { ...state, isSelecting: action.payload };
    case "SET_SAVED":
      return { ...state, isSaved: action.payload };
    case "SET_SELECTED_SERVER":
      return {
        ...state,
        selectedServer: action.payload,
        selectedServerId: action.payload?.machineIdentifier || "",
      };
    case "RESET":
      return initialSelectionState;
    default:
      return state;
  }
}

// Hook Options Interface
interface UsePlexManagementOptions {
  userId?: string;
  onAuthSuccess?: (data: unknown) => void;
  onAuthError?: (error: PlexError) => void;
}

/**
 * Consolidated Plex Management Hook
 * Combines OAuth, server management, and selection with React Query optimization.
 */
export const usePlexManagement = (options: UsePlexManagementOptions = {}) => {
  const { userId, onAuthSuccess, onAuthError } = options;

  const [selectionState, dispatch] = useReducer(
    serverSelectionReducer,
    initialSelectionState,
  );

  // Auth queries and mutations
  const {
    data: authData,
    isLoading: authLoading,
    error: authError,
    refetch: refetchAuth,
  } = usePlexAuthValidationQuery();
  const pinMutation = usePlexPinMutation();
  const pinCheckMutation = usePlexPinCheckMutation();
  const logoutMutation = usePlexLogoutMutation();

  // Auth state
  const [pinData, setPinData] = useState<PlexPinResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Auth refs for polling
  const pollingIntervalRef = useRef<number | null>(null);
  const pollingAttemptRef = useRef(0);
  const authWindowRef = useRef<Window | null>(null);

  // Derived auth state
  const isAuthenticated = authData?.valid && authData?.auth_method === "oauth";
  const username = authData?.username;
  const email = authData?.email;
  const authErrorParsed = authError ? parseAxiosError(authError) : undefined;

  // Server queries and mutations
  const {
    data: serversResponse,
    isLoading: serversLoading,
    error: serversError,
    refetch: refetchServers,
  } = usePlexServersQuery(userId);
  const {
    data: selectedServerResponse,
    isLoading: selectedServerLoading,
    refetch: refetchSelectedServer,
  } = usePlexSelectedServerQuery(userId);
  const connectionTestMutation = usePlexConnectionTestMutation();
  const serverSelectionMutation = usePlexServerSelectionMutation();

  // Server state
  const [processedServers, setProcessedServers] = useState<PlexServer[]>([]);

  // Process servers data
  const rawServers: PlexServer[] = useMemo(
    () => serversResponse?.servers || [],
    [serversResponse?.servers],
  );

  const selectedServer = selectedServerResponse?.server || null;
  const servers = processedServers.length > 0 ? processedServers : rawServers;

  // Reset processed servers when raw servers change
  useEffect(() => {
    if (rawServers.length === 0) {
      setProcessedServers([]);
    }
  }, [rawServers]);

  // === AUTH FUNCTIONS ===

  // Auth cleanup function
  const authCleanup = useCallback(() => {
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

  // Start PIN polling with optimistic updates
  const startPolling = useCallback(
    (pinId: string) => {
      if (pollingIntervalRef.current) return;

      setIsPolling(true);
      pollingAttemptRef.current = 0;

      pollingIntervalRef.current = window.setInterval(async () => {
        pollingAttemptRef.current++;

        if (
          pollingAttemptRef.current >= PLEX_AUTH_CONFIG.MAX_POLLING_ATTEMPTS
        ) {
          authCleanup();
          const timeoutError: PlexError = {
            message: "Authentication timeout. Please try again.",
            code: PLEX_ERROR_CODES.AUTH_TIMEOUT,
          };
          onAuthError?.(timeoutError);
          return;
        }

        try {
          const result = await pinCheckMutation.mutateAsync(pinId);
          if (result.authenticated) {
            authCleanup();
            await refetchAuth(); // Optimistic: refetch auth immediately
            onAuthSuccess?.(result);
          }
        } catch (pinError) {
          const plexError = parseAxiosError(pinError);
          if (plexError.code === PLEX_ERROR_CODES.PIN_EXPIRED) {
            authCleanup();
            onAuthError?.(plexError);
          }
        }
      }, PLEX_AUTH_CONFIG.POLLING_INTERVAL_MS);
    },
    [pinCheckMutation, authCleanup, onAuthSuccess, onAuthError, refetchAuth],
  );

  // Open auth window
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
      authCleanup();
      const pin = await pinMutation.mutateAsync();
      setPinData(pin);

      authWindowRef.current = openAuthWindow(pin.authUrl);
      startPolling(pin.pinId);

      return pin;
    } catch (pinError) {
      const plexError = parseAxiosError(pinError);
      onAuthError?.(plexError);
      return null;
    }
  }, [pinMutation, startPolling, authCleanup, openAuthWindow, onAuthError]);

  // Logout
  const logout = useCallback(async () => {
    try {
      authCleanup();
      await logoutMutation.mutateAsync();
      dispatch({ type: "RESET" }); // Reset server selection on logout
    } catch (logoutError) {
      const plexError = parseAxiosError(logoutError);
      onAuthError?.(plexError);
    }
  }, [logoutMutation, authCleanup, onAuthError]);

  // Cancel authentication
  const cancelAuth = useCallback(() => {
    authCleanup();
  }, [authCleanup]);

  // === SERVER FUNCTIONS ===

  // Test single connection with optimistic caching
  const testConnection = useCallback(
    async (connection: PlexServerConnection): Promise<void> => {
      try {
        const result = await connectionTestMutation.mutateAsync(connection.uri);
        connection.available = result.success;
        connection.latency = result.latency;
      } catch (error) {
        connection.available = false;
        connection.latency = undefined;
      }
    },
    [connectionTestMutation],
  );

  // Get best connection (local + low latency priority)
  const getBestConnection = useCallback(
    (connections: PlexServerConnection[]): PlexServerConnection | null => {
      const availableConnections = connections.filter((c) => c.available);
      if (availableConnections.length === 0) return null;

      return availableConnections.sort((a, b) => {
        // Prioritize local connections
        if (a.local && !b.local) return -1;
        if (!a.local && b.local) return 1;

        // Then sort by latency
        const aLatency = a.latency || 999999;
        const bLatency = b.latency || 999999;
        return aLatency - bLatency;
      })[0];
    },
    [],
  );

  // Fetch and process servers with parallel connection testing
  const fetchServers = useCallback(async () => {
    try {
      const response = await refetchServers();
      if (response.data?.servers) {
        // Parallel processing: test all connections simultaneously
        const serversWithConnections = await Promise.all(
          response.data.servers.map(async (server: PlexServer) => {
            const connectionsWithLatency = await Promise.all(
              server.connections.map(async (conn: PlexServerConnection) => {
                const connectionCopy = { ...conn };
                await testConnection(connectionCopy);
                return connectionCopy;
              }),
            );

            return {
              ...server,
              connections: connectionsWithLatency,
              bestConnection: getBestConnection(connectionsWithLatency),
            };
          }),
        );

        // Sort: available connections first
        serversWithConnections.sort((a: PlexServer, b: PlexServer) => {
          const aHasConnection = !!a.bestConnection;
          const bHasConnection = !!b.bestConnection;
          if (aHasConnection && !bHasConnection) return -1;
          if (!aHasConnection && bHasConnection) return 1;
          return 0;
        });

        setProcessedServers(serversWithConnections);
        return serversWithConnections;
      }
    } catch (error) {
      const errorMessage = parseAxiosError(error).message;
      throw new Error(`Failed to fetch servers: ${errorMessage}`);
    }
    return [];
  }, [refetchServers, testConnection, getBestConnection]);

  // Select server with optimistic updates
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

      // Optimistic update: immediately update selection state
      dispatch({ type: "SET_SELECTED_SERVER", payload: server });
      dispatch({ type: "SET_SELECTING", payload: true });

      try {
        await serverSelectionMutation.mutateAsync({
          machineIdentifier,
          name: server.name,
          uri: server.bestConnection.uri,
          local: server.bestConnection.local,
          userId,
        });
        dispatch({ type: "SET_SAVED", payload: true });
      } catch (error) {
        // Revert optimistic update on error
        dispatch({ type: "SET_SELECTED_SERVER", payload: null });
        throw error;
      } finally {
        dispatch({ type: "SET_SELECTING", payload: false });
      }
    },
    [servers, serverSelectionMutation, userId],
  );

  // === SERVER SELECTION FUNCTIONS ===

  const setSelectedServerId = useCallback((serverId: string) => {
    dispatch({ type: "SET_SELECTED_SERVER_ID", payload: serverId });
  }, []);

  const setSelecting = useCallback((selecting: boolean) => {
    dispatch({ type: "SET_SELECTING", payload: selecting });
  }, []);

  const setSaved = useCallback((saved: boolean) => {
    dispatch({ type: "SET_SAVED", payload: saved });
  }, []);

  const setSelectedServerState = useCallback((server: PlexServer | null) => {
    dispatch({ type: "SET_SELECTED_SERVER", payload: server });
  }, []);

  const resetSelection = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  // === CLEANUP ===

  useEffect(() => {
    return authCleanup;
  }, [authCleanup]);

  // === RETURN CONSOLIDATED API ===

  return {
    // Authentication
    auth: {
      isAuthenticated: !!isAuthenticated,
      isLoading:
        authLoading || pinMutation.isPending || logoutMutation.isPending,
      username,
      email,
      error: authErrorParsed,
      pinData,
      isPolling,
      startAuth,
      checkAuthStatus: refetchAuth,
      logout,
      cancelAuth,
    },

    // Server Management
    servers: {
      list: servers,
      selected: selectedServer,
      isLoading:
        serversLoading ||
        selectedServerLoading ||
        serverSelectionMutation.isPending,
      error: serversError ? parseAxiosError(serversError).message : undefined,
      fetchServers,
      refreshServers: fetchServers,
      selectServer,
      getSelectedServer: refetchSelectedServer,
    },

    // Server Selection UI State
    selection: {
      selectedServerId: selectionState.selectedServerId,
      isSelecting: selectionState.isSelecting,
      isSaved: selectionState.isSaved,
      selectedServer: selectionState.selectedServer,
      setSelectedServerId,
      setSelecting,
      setSaved,
      setSelectedServer: setSelectedServerState,
      reset: resetSelection,
    },

    // Global Loading State
    isLoading:
      authLoading ||
      serversLoading ||
      selectedServerLoading ||
      pinMutation.isPending ||
      logoutMutation.isPending ||
      serverSelectionMutation.isPending ||
      connectionTestMutation.isPending,
  };
};
