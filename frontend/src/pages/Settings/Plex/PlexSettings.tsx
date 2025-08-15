import { Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import {
  usePlexAuthValidationQuery,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
} from "@/apis/hooks/plex";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";

import AuthSection from "./AuthSection";
import ServerSection from "./ServerSection";

export const PlexSettings = () => {
  const form = useForm({
    initialValues: {
      selectedServer: null as Plex.Server | null,
      isSelecting: false,
      isSaved: false,
    },
  });

  const { values, setFieldValue } = form;
  const { setValue } = useFormActions();

  // Get authentication status
  const { data: authData, refetch: refetchAuth } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  // Get servers data
  const {
    data: servers = [],
    error: serversError,
    refetch: refetchServers,
  } = usePlexServersQuery({ enabled: isAuthenticated });

  // Get selected server from backend
  const { data: savedSelectedServer } = usePlexSelectedServerQuery({
    enabled: isAuthenticated,
  });

  // Server selection mutation
  const { mutateAsync: selectServer } = usePlexServerSelectionMutation();

  // Simple handlers without useCallback
  const handleServerSelect = async () => {
    const selectedServer = values.selectedServer;
    if (!selectedServer) return;

    setFieldValue("isSelecting", true);
    try {
      if (selectedServer.bestConnection) {
        await selectServer({
          machineIdentifier: selectedServer.machineIdentifier,
          name: selectedServer.name,
          uri: selectedServer.bestConnection.uri,
          local: selectedServer.bestConnection.local,
        });
        setFieldValue("isSaved", true);

        // Save to Bazarr settings
        setValue(selectedServer.bestConnection.uri, "plex_server");
        setValue(selectedServer.name, "plex_server_name");
      }
    } catch {
      // Error is handled by the hook
    } finally {
      setFieldValue("isSelecting", false);
    }
  };

  const handleLogout = () => {
    form.reset();
  };

  const handleCancelAuth = () => {
    // Refetch auth status when auth is cancelled
    void refetchAuth();
  };

  // Initialize selected server from saved server (without useEffect)
  if (savedSelectedServer && !values.selectedServer && !values.isSaved) {
    setFieldValue("selectedServer", savedSelectedServer);
    setFieldValue("isSaved", true);
  }

  // Auto-select single server (without useEffect)
  if (
    isAuthenticated &&
    servers.length === 1 &&
    servers[0].bestConnection &&
    !values.selectedServer &&
    !values.isSaved &&
    !savedSelectedServer
  ) {
    const server = servers[0];
    setFieldValue("selectedServer", server);
    // Auto-select the server
    void selectServer({
      machineIdentifier: server.machineIdentifier,
      name: server.name,
      uri: server.bestConnection!.uri,
      local: server.bestConnection!.local,
    }).then(() => {
      setFieldValue("isSaved", true);
      // Save to Bazarr settings
      setValue(server.bestConnection!.uri, "plex_server");
      setValue(server.name, "plex_server_name");
    });
  }

  return (
    <Stack gap="lg">
      <AuthSection onCancelAuth={handleCancelAuth} onLogout={handleLogout} />
      <ServerSection
        isAuthenticated={isAuthenticated}
        servers={servers}
        error={serversError?.message}
        selectedServer={values.selectedServer}
        isSelecting={values.isSelecting}
        isSaved={values.isSaved}
        onFetchServers={refetchServers}
        onServerSelect={handleServerSelect}
        onSelectedServerChange={(server: Plex.Server | null) =>
          setFieldValue("selectedServer", server)
        }
      />
    </Stack>
  );
};

export default PlexSettings;
