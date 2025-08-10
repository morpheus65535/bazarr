import { useCallback, useEffect, useMemo, useState } from "react";
import {
  type PlexServer,
  type PlexServerConnection,
  usePlexConnectionTestMutation,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
} from "@/plex/queries/plex";
import { parseAxiosError } from "@/plex/utilities/errors";
import { plexServerCache } from "@/plex/utilities/serverCache";

export const usePlexServers = () => {
  // Queries
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

  // Mutations
  const connectionTestMutation = usePlexConnectionTestMutation();
  const serverSelectionMutation = usePlexServerSelectionMutation();

  // State for processed servers
  const [processedServers, setProcessedServers] = useState<PlexServer[]>([]);

  // Process servers data
  const rawServers: PlexServer[] = useMemo(
    () => serversResponse?.servers || [],
    [serversResponse?.servers],
  );
  const selectedServer = selectedServerResponse?.server || null;

  // Use processed servers when available, fall back to raw servers
  const servers = processedServers.length > 0 ? processedServers : rawServers;

  // Reset processed servers when raw servers change
  useEffect(() => {
    if (rawServers.length === 0) {
      setProcessedServers([]);
    }
  }, [rawServers]);

  // Test a single connection
  const testConnection = useCallback(
    async (connection: PlexServerConnection): Promise<void> => {
      try {
        const result = await connectionTestMutation.mutateAsync(connection.uri);
        connection.available = result.success;
        connection.latency = result.latency;
      } catch (error) {
        // Log connection test failure for debugging, but don't block the process
        // In production, this could be sent to a logging service
        connection.available = false;
        connection.latency = undefined;
      }
    },
    [connectionTestMutation],
  );

  // Get best connection for a server
  const getBestConnection = useCallback(
    (connections: PlexServerConnection[]): PlexServerConnection | null => {
      const availableConnections = connections.filter((c) => c.available);
      if (availableConnections.length === 0) return null;

      // Sort by: local first, then by latency
      return availableConnections.sort((a, b) => {
        // Prioritize local connections
        if (a.local && !b.local) return -1;
        if (!a.local && b.local) return 1;

        // Then sort by latency (if available)
        const aLatency = a.latency || 999999;
        const bLatency = b.latency || 999999;
        return aLatency - bLatency;
      })[0];
    },
    [],
  );

  // Throttled fetchServers with connection testing
  const fetchServers = useCallback(async () => {
    if (plexServerCache.shouldThrottleFetch()) {
      // Throttle: only fetch every 30 seconds
      return servers;
    }
    plexServerCache.setLastFetch(Date.now());
    try {
      const response = await refetchServers();
      if (response.data?.servers) {
        // Create mutable copies and test connections in parallel for each server
        const serversWithConnections = await Promise.all(
          response.data.servers.map(async (server: PlexServer) => {
            // Create mutable copies of connections
            const connectionsWithLatency = await Promise.all(
              server.connections.map(async (conn: PlexServerConnection) => {
                const connectionCopy = { ...conn };
                await testConnection(connectionCopy);
                return connectionCopy;
              }),
            );
            // Create server copy with tested connections
            const serverCopy = {
              ...server,
              connections: connectionsWithLatency,
              bestConnection: getBestConnection(connectionsWithLatency),
            };
            return serverCopy;
          }),
        );
        // Sort servers: ones with available connections first
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
      // Parse and re-throw the error with better context for the UI
      const errorMessage = parseAxiosError(error).message;
      throw new Error(`Failed to fetch servers: ${errorMessage}`);
    }
    return [];
  }, [refetchServers, testConnection, getBestConnection, servers]);

  // Select a server and cache it
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
      plexServerCache.setSelectedServer(server);
    },
    [servers, serverSelectionMutation],
  );

  // Get selected server (refresh from server)
  const getSelectedServer = useCallback(async () => {
    try {
      const response = await refetchSelectedServer();
      return response.data?.server || null;
    } catch (error) {
      // Return null on error, letting the UI handle the fallback gracefully
      return null;
    }
  }, [refetchSelectedServer]);

  return {
    servers,
    selectedServer,
    isLoading:
      serversLoading ||
      selectedServerLoading ||
      serverSelectionMutation.isPending,
    error: serversError ? parseAxiosError(serversError).message : undefined,
    fetchServers,
    refreshServers: fetchServers,
    selectServer,
    getSelectedServer,
  };
};
