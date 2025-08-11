import React from "react";
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
import type { PlexServer } from "@/plex/queries/plex";
import { PlexConnectionCard } from "./PlexConnectionCard";
import styles from "./PlexSettings.module.scss";

interface PlexServerSectionProps {
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

export const PlexServerSection: React.FC<PlexServerSectionProps> = ({
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
              <PlexConnectionCard
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
              <PlexConnectionCard
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
