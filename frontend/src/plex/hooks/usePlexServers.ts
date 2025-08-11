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

export const usePlexServers = () => {
  const { data: serversResponse, isLoading: serversLoading, error: serversError, refetch: refetchServers } = usePlexServersQuery();
  const { data: selectedServerResponse, isLoading: selectedServerLoading, refetch: refetchSelectedServer } = usePlexSelectedServerQuery();
  const connectionTestMutation = usePlexConnectionTestMutation();
  const serverSelectionMutation = usePlexServerSelectionMutation();

  // Local enriched state (latency + availability). Simpler: enrich once per fetch.
  const [enriched, setEnriched] = useState<PlexServer[]>([]);
  const rawServers: PlexServer[] = useMemo(() => serversResponse?.servers || [], [serversResponse?.servers]);
  const selectedServer = selectedServerResponse?.server || null;

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

  const fetchServers = useCallback(async () => {
    try {
      const response = await refetchServers();
      if (!response.data?.servers) return [];
      const enrichedServers = await Promise.all(
        response.data.servers.map(async (server: PlexServer) => {
          const connections = await Promise.all(
            server.connections.map(async (c: PlexServerConnection) => {
              const copy = { ...c };
              await testConnection(copy);
              return copy;
            }),
          );
            const serverCopy = { ...server, connections, bestConnection: getBestConnection(connections) };
            return serverCopy;
        }),
      );
      enrichedServers.sort((a, b) => Number(!b.bestConnection) - Number(!a.bestConnection));
      setEnriched(enrichedServers);
      return enrichedServers;
    } catch (e) {
      const errorMessage = parseAxiosError(e).message;
      throw new Error(`Failed to fetch servers: ${errorMessage}`);
    }
  }, [refetchServers, testConnection, getBestConnection]);

  const servers = enriched.length ? enriched : rawServers; // raw until enriched

  const selectServer = useCallback(async (machineIdentifier: string) => {
    const server = servers.find((s) => s.machineIdentifier === machineIdentifier);
    if (!server) throw new Error(`Server '${machineIdentifier}' not found`);
    if (!server.bestConnection) throw new Error(`Server '${server.name}' unavailable`);
    await serverSelectionMutation.mutateAsync({
      machineIdentifier,
      name: server.name,
      uri: server.bestConnection.uri,
      local: server.bestConnection.local,
    });
  }, [servers, serverSelectionMutation]);

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
    isLoading: serversLoading || selectedServerLoading || serverSelectionMutation.isPending,
    error: serversError ? parseAxiosError(serversError).message : undefined,
    fetchServers,
    selectServer,
    getSelectedServer,
  };
};
