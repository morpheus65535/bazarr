import React, { useCallback, useContext, useRef, useState } from "react";
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Group,
  Paper,
  Select,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { faRefresh } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useQueryClient } from "@tanstack/react-query";
import {
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckQuery,
  usePlexPinMutation,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
  type PlexServer,
  type PlexServerConnection,
} from "@/apis/hooks/plex";
import { QueryKeys } from "@/apis/queries/keys";
import { FormContext } from "@/pages/Settings/utilities/FormValues";
import { PLEX_AUTH_CONFIG } from "@/constants/plex";
import styles from "./PlexSettings.module.scss";

export const PlexSettings: React.FC = () => {
  const queryClient = useQueryClient();
  const form = useContext(FormContext);
  const authWindowRef = useRef<Window | null>(null);
  const [selectedServerId, setSelectedServerId] = useState<string | null>(null);

  // Direct React Query usage - no custom hooks
  const { data: authData, isLoading: authLoading } =
    usePlexAuthValidationQuery();
  const { data: servers = [], refetch: refetchServers } = usePlexServersQuery({
    enabled: authData?.valid && authData?.auth_method === "oauth",
    select: (data: any) => {
      if (!data?.servers) return [];
      return data.servers
        .map((server: PlexServer) => ({
          ...server,
          bestConnection: getBestConnection(server.connections),
        }))
        .sort((a: PlexServer, b: PlexServer) => {
          const aHasConnection = !!a.bestConnection;
          const bHasConnection = !!b.bestConnection;
          if (aHasConnection && !bHasConnection) return -1;
          if (!aHasConnection && bHasConnection) return 1;
          return 0;
        });
    },
  });
  const { data: selectedServer } = usePlexSelectedServerQuery({
    enabled: authData?.valid && authData?.auth_method === "oauth",
    select: (data: any) => data?.server || null,
  });

  const pinMutation = usePlexPinMutation();
  const logoutMutation = usePlexLogoutMutation();
  const serverSelectionMutation = usePlexServerSelectionMutation();

  // Start PIN check polling when we have a PIN
  const { data: pinCheckData } = usePlexPinCheckQuery(
    pinMutation.data?.pinId || null,
    !!pinMutation.data?.pinId,
  );

  const isAuthenticated = authData?.valid && authData?.auth_method === "oauth";

  // Helper function for server connections
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

  // Auth handlers
  const handleStartAuth = useCallback(async () => {
    try {
      const pin = await pinMutation.mutateAsync();
      const { width, height, features } = PLEX_AUTH_CONFIG.AUTH_WINDOW_CONFIG;
      const left = Math.round(window.screen.width / 2 - width / 2);
      const top = Math.round(window.screen.height / 2 - height / 2);

      authWindowRef.current = window.open(
        pin.authUrl,
        "PlexAuth",
        `width=${width},height=${height},left=${left},top=${top},${features}`,
      );
    } catch (error) {
      console.error("Failed to start auth:", error);
    }
  }, [pinMutation]);

  const handleCancelAuth = useCallback(() => {
    if (authWindowRef.current && !authWindowRef.current.closed) {
      authWindowRef.current.close();
    }
    pinMutation.reset();
  }, [pinMutation]);

  const handleLogout = useCallback(async () => {
    try {
      await logoutMutation.mutateAsync();
      queryClient.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Settings],
      });
      if (form) {
        form.reset();
      }
    } catch (error) {
      console.error("Logout failed:", error);
    }
  }, [logoutMutation, queryClient, form]);

  // Server selection
  const handleServerSelect = useCallback(
    async (machineIdentifier: string) => {
      const server = servers.find(
        (s: PlexServer) => s.machineIdentifier === machineIdentifier,
      );
      if (!server || !server.bestConnection) return;

      try {
        await serverSelectionMutation.mutateAsync({
          machineIdentifier,
          name: server.name,
          uri: server.bestConnection.uri,
          local: server.bestConnection.local,
        });
      } catch (error) {
        console.error("Server selection failed:", error);
      }
    },
    [servers, serverSelectionMutation],
  );

  // Handle successful authentication
  React.useEffect(() => {
    if (pinCheckData?.authenticated && authWindowRef.current) {
      authWindowRef.current.close();
      pinMutation.reset();
      queryClient.invalidateQueries({
        queryKey: [QueryKeys.Plex, "auth", "validate"],
      });
    }
  }, [pinCheckData, pinMutation, queryClient]);

  return (
    <Stack gap="lg">
      {/* Authentication Section */}
      <Paper withBorder radius="md" p="lg" className={styles.authSection}>
        <Stack gap="md">
          <Title order={4}>Plex OAuth (recommended)</Title>

          {authLoading && <Text>Loading authentication status...</Text>}

          {!isAuthenticated && !authLoading && (
            <Stack gap="sm">
              {pinMutation.data && !pinCheckData?.authenticated && (
                <>
                  <Text size="lg" fw={600}>
                    Complete Authentication
                  </Text>
                  <Text>
                    PIN Code:{" "}
                    <Text component="span" fw={700}>
                      {pinMutation.data.code}
                    </Text>
                  </Text>
                  <Text size="sm">
                    Complete the authentication in the opened window.
                  </Text>
                  <Button
                    onClick={handleCancelAuth}
                    variant="light"
                    color="gray"
                    size="sm"
                  >
                    Cancel
                  </Button>
                </>
              )}

              {!pinMutation.data && (
                <>
                  <Text size="sm">
                    Connect your Plex account to enable secure, automated
                    integration with Bazarr.
                  </Text>
                  <Button
                    onClick={handleStartAuth}
                    variant="filled"
                    color="brand"
                    size="md"
                    loading={pinMutation.isPending}
                  >
                    Connect to Plex
                  </Button>
                </>
              )}
            </Stack>
          )}

          {isAuthenticated && (
            <>
              <Alert color="brand" variant="light">
                Connected as {authData.username} ({authData.email})
              </Alert>
              <Button
                onClick={handleLogout}
                variant="light"
                color="gray"
                size="sm"
                loading={logoutMutation.isPending}
              >
                Disconnect from Plex
              </Button>
            </>
          )}
        </Stack>
      </Paper>

      {/* Server Section */}
      {isAuthenticated && (
        <Paper withBorder radius="md" p="lg" className={styles.serverSection}>
          <Stack gap="lg">
            <Title order={4}>Plex Servers</Title>

            {servers.length === 0 ? (
              <Badge size="md">Testing server connections...</Badge>
            ) : servers.length === 1 ? (
              <Stack gap="md">
                <Group justify="space-between" align="center">
                  <Text>
                    {servers[0].name} ({servers[0].platform} - v
                    {servers[0].version})
                  </Text>
                  {selectedServer?.machineIdentifier ===
                  servers[0].machineIdentifier ? (
                    <Badge color="green" size="sm">
                      Connected
                    </Badge>
                  ) : !servers[0].bestConnection ? (
                    <Badge color="red" size="sm">
                      Unavailable
                    </Badge>
                  ) : null}
                  <ActionIcon
                    variant="light"
                    color="gray"
                    size="lg"
                    onClick={() => refetchServers()}
                    title="Refresh server list"
                  >
                    <FontAwesomeIcon icon={faRefresh} size="sm" />
                  </ActionIcon>
                </Group>
                {servers[0].bestConnection &&
                  selectedServer?.machineIdentifier !==
                    servers[0].machineIdentifier && (
                    <Button
                      onClick={() =>
                        handleServerSelect(servers[0].machineIdentifier)
                      }
                      loading={serverSelectionMutation.isPending}
                    >
                      Connect to Server
                    </Button>
                  )}
              </Stack>
            ) : (
              <Group className={styles.serverSelectGroup}>
                <Select
                  label="Select server"
                  placeholder="Choose a server..."
                  data={servers.map((server: PlexServer) => ({
                    value: server.machineIdentifier,
                    label: `${server.name} (${server.platform} - v${server.version})${!server.bestConnection ? " (Unavailable)" : ""}`,
                    disabled: !server.bestConnection,
                  }))}
                  value={
                    selectedServerId ||
                    selectedServer?.machineIdentifier ||
                    null
                  }
                  onChange={(value: string | null) =>
                    setSelectedServerId(value)
                  }
                  className={styles.serverSelectField}
                  searchable
                />
                <Button
                  variant="filled"
                  color="brand"
                  disabled={!selectedServerId}
                  loading={serverSelectionMutation.isPending}
                  onClick={() =>
                    selectedServerId && handleServerSelect(selectedServerId)
                  }
                >
                  Select Server
                </Button>
                <ActionIcon
                  variant="light"
                  color="gray"
                  size="lg"
                  onClick={() => refetchServers()}
                  className={styles.refreshButton}
                  title="Refresh server list"
                >
                  <FontAwesomeIcon icon={faRefresh} size="sm" />
                </ActionIcon>
              </Group>
            )}
          </Stack>
        </Paper>
      )}
    </Stack>
  );
};

export default PlexSettings;
