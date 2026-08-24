import { FC } from "react";
import { Badge, Card, Group, Stack, Text } from "@mantine/core";

interface ConnectionsCardProps {
  servers: Plex.Server[];
  selectedServerId: string;
}

const ConnectionsCard: FC<ConnectionsCardProps> = ({
  servers,
  selectedServerId,
}) => {
  const server = servers.find(
    (s: Plex.Server) => s.machineIdentifier === selectedServerId,
  );

  if (!server) return null;

  return (
    <Card withBorder p="md" radius="sm">
      <Text size="sm" fw={600} mb="xs">
        Verified Connections:
      </Text>
      <Stack gap="xs">
        {server.connections.map((conn: Plex.ServerConnection, idx: number) => (
          <Group gap="xs" key={`${conn.uri}-${idx}`}>
            <Text size="sm" fw={700} c={conn.available ? "success" : "danger"}>
              {conn.available ? "✓" : "✗"}
            </Text>
            <Text size="sm">
              {conn.uri}
              {conn.local && " (Local)"}
            </Text>
            {conn.available && conn.latency && (
              <Badge size="sm" variant="light">
                {conn.latency}ms
              </Badge>
            )}
          </Group>
        ))}
      </Stack>
    </Card>
  );
};

export default ConnectionsCard;
