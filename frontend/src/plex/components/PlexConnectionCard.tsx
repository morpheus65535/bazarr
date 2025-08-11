import React from "react";
import { Badge, Card, Group, Stack, Text } from "@mantine/core";
import type { PlexServer, PlexServerConnection } from "@/plex/queries/plex";
import styles from "./PlexSettings.module.scss";

interface PlexConnectionCardProps {
  servers: PlexServer[];
  selectedServerId: string;
}

export const PlexConnectionCard: React.FC<PlexConnectionCardProps> = ({
  servers,
  selectedServerId,
}) => {
  const server = servers.find(
    (s: PlexServer) => s.machineIdentifier === selectedServerId,
  );

  if (!server) return null;

  // Enhanced connection status with latency color coding
  const getLatencyColor = (latency?: number): string => {
    if (!latency) return "gray";
    if (latency < 100) return "green";
    if (latency < 300) return "yellow";
    return "red";
  };

  return (
    <Card withBorder p="md" radius="md" className={styles.serverConnectionCard}>
      <Text size="sm" fw={600} mb="xs">
        Available Connections:
      </Text>
      <Stack gap="xs">
        {server.connections.map((conn: PlexServerConnection, idx: number) => (
          <Group gap="xs" key={`${conn.uri}-${idx}`} align="center">
            <Text
              size="sm"
              className={`${styles.connectionIndicator} ${
                conn.available ? styles.success : styles.error
              }`}
            >
              {conn.available ? "✓" : "✗"}
            </Text>
            <Text size="sm" style={{ flex: 1 }}>
              {conn.uri}
              {conn.local && " (Local)"}
            </Text>
            {conn.latency && (
              <Badge
                size="sm"
                color={getLatencyColor(conn.latency)}
                variant={conn.local ? "filled" : "light"}
              >
                {conn.latency}ms {conn.local && "🏠"}
              </Badge>
            )}
          </Group>
        ))}
      </Stack>
    </Card>
  );
};
