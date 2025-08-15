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
import ConnectionsCard from "./ConnectionsCard";
import styles from "@/pages/Settings/Plex/PlexSettings.module.scss";

interface ServerSectionProps {
  isAuthenticated: boolean;
  servers: Plex.Server[];
  error?: string;
  selectedServer: Plex.Server | null;
  isSelecting: boolean;
  isSaved: boolean;
  onFetchServers: () => void;
  onServerSelect: () => void;
  onSelectedServerChange: (server: Plex.Server | null) => void;
}

const ServerSection = ({
  isAuthenticated,
  servers,
  error,
  selectedServer,
  isSelecting,
  isSaved,
  onFetchServers,
  onServerSelect,
  onSelectedServerChange,
}: ServerSectionProps) => {
  if (!isAuthenticated) {
    return null;
  }

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
                data={servers.map((server: Plex.Server) => ({
                  value: server.machineIdentifier,
                  label: `${server.name} (${server.platform} - v${server.version})${!server.bestConnection ? " (Unavailable)" : ""}`,
                  disabled: !server.bestConnection,
                }))}
                value={selectedServer?.machineIdentifier || null}
                onChange={(value: string | null) => {
                  const server = value
                    ? servers.find(
                        (s: Plex.Server) => s.machineIdentifier === value,
                      ) || null
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
                  (s: Plex.Server) =>
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

export default ServerSection;
