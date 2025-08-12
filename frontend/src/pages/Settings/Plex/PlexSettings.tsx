import React, { useCallback, useContext, useEffect } from "react";
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
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
import { usePlexOAuth } from "@/apis/hooks/usePlexOAuth";
import { usePlexServers } from "@/apis/hooks/usePlexServers";
import { useServerSelection } from "@/apis/hooks/useServerSelection";
import { QueryKeys } from "@/apis/queries/keys";
import { FormContext } from "@/pages/Settings/utilities/FormValues";
import type { PlexServer, PlexServerConnection } from "@/plex/queries/plex";
import { getErrorMessage, type PlexError } from "@/plex/utilities/errors";
import styles from "./PlexSettings.module.scss";

interface AuthSectionProps {
  isLoading: boolean;
  isPolling: boolean;
  isAuthenticated: boolean;
  pinData?: { code: string } | null;
  authError?: PlexError;
  username?: string;
  email?: string;
  onStartAuth: () => void;
  onCancelAuth: () => void;
  onLogout: () => void;
}

const AuthSection: React.FC<AuthSectionProps> = ({
  isLoading,
  isPolling,
  isAuthenticated,
  pinData,
  authError,
  username,
  email,
  onStartAuth,
  onCancelAuth,
  onLogout,
}) => {
  if (isLoading && !isPolling) {
    return <Text>Loading authentication status...</Text>;
  }

  if (isPolling && pinData) {
    return (
      <Paper withBorder radius="md" p="lg" className={styles.authSection}>
        <Stack gap="md">
          <Title order={4}>Plex OAuth (recommended)</Title>
          <Stack gap="sm">
            <Text size="lg" fw={600}>
              Complete Authentication
            </Text>
            <Text>
              PIN Code:{" "}
              <Text component="span" fw={700}>
                {pinData.code}
              </Text>
            </Text>
            <Text size="sm">
              Complete the authentication in the opened window.
            </Text>
            <Button
              onClick={onCancelAuth}
              variant="light"
              color="gray"
              size="sm"
              className={styles.actionButton}
            >
              Cancel
            </Button>
          </Stack>
        </Stack>
      </Paper>
    );
  }

  if (!isAuthenticated) {
    return (
      <Paper withBorder radius="md" p="lg" className={styles.authSection}>
        <Stack gap="md">
          <Title order={4}>Plex OAuth (recommended)</Title>
          <Stack gap="sm">
            <Text size="sm">
              Connect your Plex account to enable secure, automated integration
              with Bazarr.
            </Text>
            {authError && (
              <Alert color="red" variant="light">
                {getErrorMessage(authError)}
              </Alert>
            )}
            <Button
              onClick={onStartAuth}
              variant="filled"
              color="brand"
              size="md"
              className={styles.actionButton}
            >
              Connect to Plex
            </Button>
          </Stack>
        </Stack>
      </Paper>
    );
  }

  // Authenticated state
  return (
    <Paper withBorder radius="md" p="lg" className={styles.authSection}>
      <Stack gap="md">
        <Title order={4}>Plex OAuth (recommended)</Title>
        <Alert color="brand" variant="light">
          Connected as {username} ({email})
        </Alert>
        <Button
          onClick={onLogout}
          variant="light"
          color="gray"
          size="sm"
          className={styles.actionButton}
        >
          Disconnect from Plex
        </Button>
      </Stack>
    </Paper>
  );
};

interface ServerSectionProps {
  isAuthenticated: boolean;
  servers: PlexServer[];
  isLoading: boolean;
  error?: string;
  selectedServerId: string;
  selectedServer?: PlexServer | null;
  isSelecting: boolean;
  isSaved: boolean;
  onFetchServers: () => void;
  onServerSelect: () => void;
  onSelectedServerIdChange: (id: string) => void;
}

const ServerSection: React.FC<ServerSectionProps> = ({
  isAuthenticated,
  servers,
  isLoading,
  error,
  selectedServerId,
  selectedServer,
  isSelecting,
  isSaved,
  onFetchServers,
  onServerSelect,
  onSelectedServerIdChange,
}) => {
  if (!isAuthenticated) return null;

  return (
    <Paper withBorder radius="md" p="lg" className={styles.serverSection}>
      <Stack gap="lg">
        <Title order={4}>Plex Servers</Title>

        {error && (
          <Alert color="red" variant="light">
            Failed to load servers: {error}
          </Alert>
        )}

        {isLoading ? (
          <Stack gap="sm">
            <Text>Loading servers...</Text>
          </Stack>
        ) : servers.length === 0 ? (
          <Stack gap="sm">
            <Text>No servers found.</Text>
            <Button onClick={onFetchServers} variant="light" color="gray">
              Refresh
            </Button>
          </Stack>
        ) : servers.length === 1 ? (
          // Single server - show simplified interface
          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Stack gap="xs" style={{ flex: 1 }}>
                <Group gap="xs">
                  <Text>
                    {servers[0].name} ({servers[0].platform} - v
                    {servers[0].version})
                  </Text>
                  {isSaved ? (
                    <Badge color="green" size="sm">
                      Connected
                    </Badge>
                  ) : !servers[0].bestConnection ? (
                    <Badge color="red" size="sm">
                      Unavailable
                    </Badge>
                  ) : null}
                </Group>
              </Stack>
              <ActionIcon
                variant="light"
                color="gray"
                size="lg"
                onClick={onFetchServers}
                title="Refresh server list"
              >
                <FontAwesomeIcon icon={faRefresh} size="sm" />
              </ActionIcon>
            </Group>
            {selectedServerId && (
              <ConnectionsCard
                servers={servers}
                selectedServerId={selectedServerId}
              />
            )}
          </Stack>
        ) : (
          // Multiple servers - show selection interface
          <Stack gap="md">
            <Group className={styles.serverSelectGroup}>
              <Select
                label="Select server"
                placeholder="Choose a server..."
                data={servers.map((server: PlexServer) => ({
                  value: server.machineIdentifier,
                  label: `${server.name} (${server.platform} - v${server.version})${!server.bestConnection ? " (Unavailable)" : ""}`,
                  disabled: !server.bestConnection,
                }))}
                value={selectedServerId}
                onChange={(value: string | null) =>
                  onSelectedServerIdChange(value || "")
                }
                className={styles.serverSelectField}
                searchable
              />
              <Button
                variant="filled"
                color="brand"
                disabled={!selectedServerId || isSelecting}
                loading={isSelecting}
                onClick={onServerSelect}
              >
                Select Server
              </Button>
              <ActionIcon
                variant="light"
                color="gray"
                size="lg"
                onClick={onFetchServers}
                className={styles.refreshButton}
                title="Refresh server list"
              >
                <FontAwesomeIcon icon={faRefresh} size="sm" />
              </ActionIcon>
            </Group>

            {isSaved && selectedServer && (
              <Alert color="brand" variant="light">
                Server saved: "{selectedServer.name}" (v
                {servers.find(
                  (s: PlexServer) =>
                    s.machineIdentifier === selectedServer.machineIdentifier,
                )?.version ||
                  selectedServer.version ||
                  "Unknown"}
                )
              </Alert>
            )}

            {selectedServerId && (
              <ConnectionsCard
                servers={servers}
                selectedServerId={selectedServerId}
              />
            )}
          </Stack>
        )}
      </Stack>
    </Paper>
  );
};

interface ConnectionsCardProps {
  servers: PlexServer[];
  selectedServerId: string;
}

const ConnectionsCard: React.FC<ConnectionsCardProps> = ({
  servers,
  selectedServerId,
}) => {
  const server = servers.find(
    (s: PlexServer) => s.machineIdentifier === selectedServerId,
  );

  if (!server) return null;

  return (
    <Card withBorder p="md" radius="md" className={styles.serverConnectionCard}>
      <Text size="sm" fw={600} mb="xs">
        Available Connections:
      </Text>
      <Stack gap="xs">
        {server.connections.map((conn: PlexServerConnection, idx: number) => (
          <Group gap="xs" key={`${conn.uri}-${idx}`}>
            <Text
              size="sm"
              className={`${styles.connectionIndicator} ${
                conn.available ? styles.success : styles.error
              }`}
            >
              {conn.available ? "✓" : "✗"}
            </Text>
            <Text size="sm">
              {conn.uri}
              {conn.local && " (Local)"}
              {conn.latency && ` - ${conn.latency}ms`}
            </Text>
          </Group>
        ))}
      </Stack>
    </Card>
  );
};

export const PlexSettings: React.FC = () => {
  const queryClient = useQueryClient();
  const form = useContext(FormContext);

  // Server selection state management
  const {
    selectedServerId,
    isSelecting,
    isSaved,
    selectedServer,
    setSelectedServerId,
    setSelecting,
    setSaved,
    setSelectedServer,
  } = useServerSelection();

  // Plex OAuth hook (React Query version)
  const {
    isAuthenticated,
    isLoading: authLoading,
    username,
    email,
    error: authError,
    pinData,
    startAuth,
    logout,
    cancelAuth,
    isPolling,
  } = usePlexOAuth({
    onAuthSuccess: handleAuthSuccess,
    onAuthError: handleAuthError,
  });

  // Plex servers hook (React Query version)
  const {
    servers,
    selectedServer: savedSelectedServer,
    isLoading: serversLoading,
    error: serversError,
    fetchServers,
    selectServer,
  } = usePlexServers();

  // Centralized server selection effect - handles all server selection logic
  useEffect(() => {
    if (!isAuthenticated) return;

    // Priority 1: Use cached server if available
    const cachedServer = (
      window as unknown as {
        bazarrPlexCache?: { selectedServer?: PlexServer | null };
      }
    )?.bazarrPlexCache?.selectedServer;

    if (cachedServer && !isSaved) {
      setSelectedServer(cachedServer);
      setSelectedServerId(cachedServer.machineIdentifier);
      setSaved(true);
      return;
    }

    // Priority 2: Use saved server from API
    if (savedSelectedServer && !isSaved) {
      setSelectedServer(savedSelectedServer);
      setSelectedServerId(savedSelectedServer.machineIdentifier);
      setSaved(true);
      return;
    }

    // Priority 3: Auto-select single available server
    if (
      servers.length === 1 &&
      servers[0].bestConnection &&
      !isSaved &&
      !savedSelectedServer &&
      !cachedServer
    ) {
      const singleServer = servers[0];
      setSelectedServerId(singleServer.machineIdentifier);

      // Auto-select the single server
      selectServer(singleServer.machineIdentifier)
        .then(() => {
          setSelectedServer(singleServer);
          setSaved(true);
        })
        .catch(() => {
          // Error is handled by the selectServer mutation
        });
    }
  }, [
    isAuthenticated,
    servers,
    savedSelectedServer,
    isSaved,
    selectServer,
    setSelectedServerId,
    setSelectedServer,
    setSaved,
  ]);

  // Success handler for OAuth authentication
  function handleAuthSuccess() {
    fetchServers();

    // Invalidate system queries to refresh settings
    queryClient.invalidateQueries({
      queryKey: [QueryKeys.System],
    });

    // Reset form properly using Promise microtask to avoid race conditions
    if (form) {
      Promise.resolve().then(() => {
        form.reset();
      });
    }
  }

  // Error handler for OAuth authentication
  function handleAuthError() {
    // Error is already handled in the hook and displayed in UI
  }

  // Fetch servers with connection testing when authenticated
  useEffect(() => {
    if (isAuthenticated && servers.length > 0) {
      fetchServers();
    }
  }, [isAuthenticated, servers.length, fetchServers]);

  // Handle server selection
  const handleServerSelect = useCallback(async () => {
    if (!selectedServerId) return;

    setSelecting(true);
    try {
      const server = servers.find(
        (s: PlexServer) => s.machineIdentifier === selectedServerId,
      );

      if (server?.bestConnection) {
        await selectServer(selectedServerId);
        setSelectedServer(server);
        setSaved(true);
      }
    } catch {
      // Error is handled by the hook
    } finally {
      setSelecting(false);
    }
  }, [
    selectedServerId,
    servers,
    selectServer,
    setSelectedServer,
    setSaved,
    setSelecting,
  ]);

  // Handle logout
  const handleLogout = useCallback(async () => {
    await logout();

    // Invalidate system queries to refresh settings
    queryClient.invalidateQueries({
      queryKey: [QueryKeys.System],
    });

    // Reset form properly
    if (form) {
      Promise.resolve().then(() => {
        form.reset();
      });
    }
  }, [logout, queryClient, form]);

  return (
    <Stack gap="lg">
      <AuthSection
        isLoading={authLoading}
        isPolling={isPolling}
        isAuthenticated={isAuthenticated}
        pinData={pinData}
        authError={authError}
        username={username}
        email={email}
        onStartAuth={startAuth}
        onCancelAuth={cancelAuth}
        onLogout={handleLogout}
      />
      <ServerSection
        isAuthenticated={isAuthenticated}
        servers={servers}
        isLoading={serversLoading}
        error={serversError}
        selectedServerId={selectedServerId}
        selectedServer={selectedServer}
        isSelecting={isSelecting}
        isSaved={isSaved}
        onFetchServers={fetchServers}
        onServerSelect={handleServerSelect}
        onSelectedServerIdChange={setSelectedServerId}
      />
    </Stack>
  );
};

export default PlexSettings;
