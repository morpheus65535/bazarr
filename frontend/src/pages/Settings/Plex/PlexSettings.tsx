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
import { useForm } from "@mantine/form";
import { faRefresh } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useQueryClient } from "@tanstack/react-query";
import { usePlexOAuth, usePlexServers } from "@/apis/hooks/plex";
import { QueryKeys } from "@/apis/queries/keys";
import type { PlexServer, PlexServerConnection } from "@/apis/queries/plex";
import { FormContext } from "@/pages/Settings/utilities/FormValues";
import styles from "./PlexSettings.module.scss";

interface AuthSectionProps {
  isLoading: boolean;
  isPolling: boolean;
  isAuthenticated: boolean;
  pinData?: { code: string } | null;
  authError?: Error;
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
                {authError.message || "Authentication failed"}
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
  error?: string;
  selectedServer: PlexServer | null;
  isSelecting: boolean;
  isSaved: boolean;
  onFetchServers: () => void;
  onServerSelect: () => void;
  onSelectedServerChange: (server: PlexServer | null) => void;
}

const ServerSection: React.FC<ServerSectionProps> = ({
  isAuthenticated,
  servers,
  error,
  selectedServer,
  isSelecting,
  isSaved,
  onFetchServers,
  onServerSelect,
  onSelectedServerChange,
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

        {isAuthenticated && servers.length === 0 && !error ? (
          <Badge size="md">Testing server connections...</Badge>
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
            {selectedServer && (
              <ConnectionsCard
                servers={servers}
                selectedServerId={selectedServer.machineIdentifier}
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
                value={selectedServer?.machineIdentifier || null}
                onChange={(value: string | null) => {
                  const server = value
                    ? servers.find((s) => s.machineIdentifier === value) || null
                    : null;
                  onSelectedServerChange(server);
                }}
                className={styles.serverSelectField}
                searchable
              />
              <Button
                variant="filled"
                color="brand"
                disabled={!selectedServer || isSelecting}
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

            {selectedServer && (
              <ConnectionsCard
                servers={servers}
                selectedServerId={selectedServer.machineIdentifier}
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
            </Text>
            {conn.available && conn.latency && (
              <Badge size="sm">{conn.latency}ms</Badge>
            )}
          </Group>
        ))}
      </Stack>
    </Card>
  );
};

export const PlexSettings: React.FC = () => {
  const queryClient = useQueryClient();
  const form = useContext(FormContext);

  // Mantine form for server selection
  const serverForm = useForm({
    initialValues: {
      selectedServer: null as PlexServer | null,
      isSelecting: false,
      isSaved: false,
    },
  });

  // Extract stable form methods to satisfy ESLint exhaustive-deps
  const { setFieldValue, values, reset } = serverForm;

  const {
    servers,
    selectedServer: savedSelectedServer,
    error: serversError,
    selectServer,
    refetchServers,
  } = usePlexServers();

  // Plex OAuth hook (React Query version)
  const {
    isAuthenticated,
    isLoading: authLoading,
    username,
    email,
    error: authError,
    pinData,
    isPolling,
    startAuth,
    logout,
    cancelAuth,
  } = usePlexOAuth({
    onAuthSuccess: () => {
      // Just refetch servers on auth success - useEffect handles the rest
      refetchServers();
    },
  });

  const performAutoSelection = useCallback(
    async (server: PlexServer) => {
      setFieldValue("selectedServer", server);
      setFieldValue("isSelecting", true);

      try {
        await selectServer(server.machineIdentifier);
        setFieldValue("isSaved", true);
      } catch {
        // Error is handled by the selectServer mutation
      } finally {
        setFieldValue("isSelecting", false);
      }
    },
    [setFieldValue, selectServer],
  );

  const handleSavedServerSelection = useCallback(
    (server: PlexServer) => {
      setFieldValue("selectedServer", server);
      setFieldValue("isSaved", true);
    },
    [setFieldValue],
  );

  const isSaved = values.isSaved;

  useEffect(() => {
    if (!isAuthenticated) return;

    if (savedSelectedServer && !isSaved) {
      handleSavedServerSelection(savedSelectedServer);
      return;
    }

    if (
      servers.length === 1 &&
      servers[0].bestConnection &&
      !isSaved &&
      !savedSelectedServer
    ) {
      const singleServer = servers[0];
      performAutoSelection(singleServer);
    }
  }, [
    isAuthenticated,
    servers,
    savedSelectedServer,
    isSaved,
    performAutoSelection,
    handleSavedServerSelection,
  ]);

  const handleServerSelect = useCallback(async () => {
    const selectedServer = values.selectedServer;
    if (!selectedServer) return;

    setFieldValue("isSelecting", true);
    try {
      if (selectedServer.bestConnection) {
        await selectServer(selectedServer.machineIdentifier);
        setFieldValue("isSaved", true);
      }
    } catch {
      // Error is handled by the hook
    } finally {
      setFieldValue("isSelecting", false);
    }
  }, [values.selectedServer, setFieldValue, selectServer]);

  const handleLogout = useCallback(async () => {
    await logout();
    reset();

    queryClient.invalidateQueries({
      queryKey: [QueryKeys.System, QueryKeys.Settings],
    });

    if (form) {
      Promise.resolve().then(() => {
        form.reset();
      });
    }
  }, [logout, reset, queryClient, form]);

  const selectedServer = values.selectedServer;

  return (
    <Stack gap="lg">
      <AuthSection
        isLoading={authLoading}
        isPolling={isPolling}
        isAuthenticated={isAuthenticated}
        pinData={pinData}
        authError={authError || undefined}
        username={username}
        email={email}
        onStartAuth={startAuth}
        onCancelAuth={cancelAuth}
        onLogout={handleLogout}
      />
      <ServerSection
        isAuthenticated={isAuthenticated}
        servers={servers}
        error={serversError}
        selectedServer={selectedServer}
        isSelecting={values.isSelecting}
        isSaved={values.isSaved}
        onFetchServers={refetchServers}
        onServerSelect={handleServerSelect}
        onSelectedServerChange={(server: PlexServer | null) =>
          setFieldValue("selectedServer", server)
        }
      />
    </Stack>
  );
};

export default PlexSettings;
