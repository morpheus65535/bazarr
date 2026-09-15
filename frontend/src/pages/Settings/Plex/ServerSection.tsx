import { useCallback, useEffect, useState } from "react";
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Group,
  Loader,
  Select,
  Stack,
  Text,
} from "@mantine/core";
import { faRefresh } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  usePlexAuthValidationQuery,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
} from "@/apis/hooks/plex";
import { Message } from "@/pages/Settings/components";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";
import ConnectionsCard from "./ConnectionsCard";

const ServerSection = () => {
  // Internal state management
  const [selectedServer, setSelectedServer] = useState<Plex.Server | null>(
    null,
  );
  const [isSelecting, setIsSelecting] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [wasAuthenticated, setWasAuthenticated] = useState(false);

  // Use hooks to fetch data internally
  const { data: authData } = usePlexAuthValidationQuery();
  const {
    data: servers = [],
    error: serversError,
    refetch: refetchServers,
    isFetching: serversFetching,
  } = usePlexServersQuery();
  const { mutateAsync: selectServerMutation } =
    usePlexServerSelectionMutation();
  const { data: savedSelectedServer } = usePlexSelectedServerQuery({
    enabled: Boolean(authData?.valid && authData?.authMethod === "oauth"),
  });
  const { setValue } = useFormActions();

  // Determine authentication status
  const isAuthenticated = Boolean(
    authData?.valid && authData?.authMethod === "oauth",
  );

  // Reset state when authentication changes from false to true
  // (re-authentication). Adjusting state during render avoids an
  // effect-driven render cascade.
  if (isAuthenticated && !wasAuthenticated) {
    setWasAuthenticated(true);
    setSelectedServer(null);
    setIsSelecting(false);
    setIsSaved(false);
  } else if (!isAuthenticated && wasAuthenticated) {
    setWasAuthenticated(false);
  }

  // Consolidated server selection and saving logic
  const selectAndSaveServer = useCallback(
    async (server: Plex.Server) => {
      if (!server.bestConnection) return;

      setIsSelecting(true);
      try {
        await selectServerMutation({
          machineIdentifier: server.machineIdentifier,
          name: server.name,
          uri: server.bestConnection.uri,
          local: server.bestConnection.local,
          connections: server.connections?.map((conn) => conn.uri) || [
            server.bestConnection.uri,
          ],
        });
        setIsSaved(true);
        // Save to Bazarr settings
        setValue(server.bestConnection.uri, "plex_server");
        setValue(server.name, "plex_server_name");
      } catch {
        // Error is handled by the mutation hook
      } finally {
        setIsSelecting(false);
      }
    },
    [selectServerMutation, setValue],
  );

  // Handle server selection
  const handleServerSelect = async () => {
    if (!selectedServer) return;
    await selectAndSaveServer(selectedServer);
  };

  // Handle server change
  const handleSelectedServerChange = (server: Plex.Server | null) => {
    setSelectedServer(server);
    setIsSaved(false);
  };

  // First priority: initialize selection from the saved server once data is
  // available (adjusting state during render avoids an effect-driven cascade).
  if (isAuthenticated && savedSelectedServer && !selectedServer && !isSaved) {
    setSelectedServer(savedSelectedServer);
    setIsSaved(true);
  }

  // Second priority: auto-select and save the single available server.
  useEffect(() => {
    if (!isAuthenticated || savedSelectedServer || selectedServer || isSaved) {
      return;
    }

    const server = servers[0];
    const bestConnection = server?.bestConnection;
    if (servers.length !== 1 || !bestConnection) {
      return;
    }

    void selectServerMutation(
      {
        machineIdentifier: server.machineIdentifier,
        name: server.name,
        uri: bestConnection.uri,
        local: bestConnection.local,
        connections: server.connections?.map((conn) => conn.uri) || [
          bestConnection.uri,
        ],
      },
      {
        onSuccess: () => {
          setSelectedServer(server);
          setIsSaved(true);
          // Save to Bazarr settings
          setValue(bestConnection.uri, "plex_server");
          setValue(server.name, "plex_server_name");
        },
      },
    );
  }, [
    isAuthenticated,
    savedSelectedServer,
    servers,
    selectedServer,
    isSaved,
    selectServerMutation,
    setValue,
  ]);

  if (!isAuthenticated) {
    return null;
  }

  const refreshButton = (
    <ActionIcon
      onClick={() => refetchServers()}
      title="Refresh server list"
      aria-label="Refresh server list"
    >
      <FontAwesomeIcon icon={faRefresh} size="sm" />
    </ActionIcon>
  );

  return (
    <Stack gap="xs">
      {serversError && (
        <Alert color="danger" variant="light">
          Failed to load servers: {serversError.message}
        </Alert>
      )}

      {servers.length === 0 && serversFetching ? (
        <Group gap="xs">
          <Loader size="xs" />
          <Text size="sm" c="dimmed">
            Testing server connections...
          </Text>
        </Group>
      ) : servers.length === 0 ? (
        <Group gap="xs" justify="space-between">
          <Message>No servers found.</Message>
          <Button
            onClick={() => refetchServers()}
            variant="light"
            color="secondary"
          >
            Refresh
          </Button>
        </Group>
      ) : servers.length === 1 ? (
        // Single server - show simplified interface
        <>
          <Group justify="space-between" align="center">
            <Group gap="xs">
              <Text>
                {servers[0].name} ({servers[0].platform} - v{servers[0].version}
                )
              </Text>
              {isSaved ? (
                <Badge color="success" size="sm">
                  Connected
                </Badge>
              ) : !servers[0].bestConnection ? (
                <Badge color="danger" size="sm">
                  Unavailable
                </Badge>
              ) : null}
            </Group>
            {refreshButton}
          </Group>
          {selectedServer && (
            <ConnectionsCard
              servers={servers}
              selectedServerId={selectedServer.machineIdentifier}
            />
          )}
        </>
      ) : (
        // Multiple servers - show selection interface
        <>
          <Group align="flex-end" wrap="nowrap">
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
                handleSelectedServerChange(server);
              }}
              searchable
              style={{ flex: 1 }}
            />
            <Button
              disabled={!selectedServer || isSelecting}
              loading={isSelecting}
              onClick={handleServerSelect}
            >
              Select Server
            </Button>
            {refreshButton}
          </Group>

          {isSaved && selectedServer && (
            <Alert color="success" variant="light">
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
        </>
      )}
    </Stack>
  );
};

export default ServerSection;
