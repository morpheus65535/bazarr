import { Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";
import {
  usePlexAuthValidationQuery,
  usePlexServersQuery,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
} from "@/apis/hooks/plex";
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

  const { setValue } = useFormActions();

  const authQuery = usePlexAuthValidationQuery();
  const serversQuery = usePlexServersQuery({
    enabled: authQuery.data?.valid && authQuery.data?.auth_method === "oauth",
  });
  const selectedServerQuery = usePlexSelectedServerQuery({
    enabled: authQuery.data?.valid && authQuery.data?.auth_method === "oauth",
  });
  const serverSelectionMutation = usePlexServerSelectionMutation();

  // Extract data from queries
  const isAuthenticated =
    authQuery.data?.valid && authQuery.data?.auth_method === "oauth";
  const servers = serversQuery.data || [];
  const serversError = serversQuery.error?.message;
  const refetchServers = serversQuery.refetch;
  const savedSelectedServer = selectedServerQuery.data;

  if (isAuthenticated && savedSelectedServer && !form.values.isSaved) {
    form.setFieldValue("selectedServer", savedSelectedServer);
    form.setFieldValue("isSaved", true);
  } else if (
    isAuthenticated &&
    servers.length === 1 &&
    servers[0].bestConnection &&
    !form.values.isSaved &&
    !savedSelectedServer
  ) {
    form.setFieldValue("selectedServer", servers[0]);
    serverSelectionMutation.mutate(
      {
        machineIdentifier: servers[0].machineIdentifier,
        name: servers[0].name,
        uri: servers[0].bestConnection.uri,
        local: servers[0].bestConnection.local,
      },
      {
        onSuccess: () => form.setFieldValue("isSaved", true),
      },
    );
  }

  const handleServerSelect = () => {
    const selectedServer = form.values.selectedServer;
    if (!selectedServer?.bestConnection) return;

    form.setFieldValue("isSelecting", true);
    serverSelectionMutation.mutate(
      {
        machineIdentifier: selectedServer.machineIdentifier,
        name: selectedServer.name,
        uri: selectedServer.bestConnection.uri,
        local: selectedServer.bestConnection.local,
      },
      {
        onSuccess: () => {
          form.setFieldValue("isSaved", true);
          form.setFieldValue("isSelecting", false);
        },
        onError: () => {
          form.setFieldValue("isSelecting", false);
        },
      },
    );
  };

  const handleLogout = () => {
    form.reset();
  };

  const handleCancelAuth = () => {
    // Handled in AuthSection
  };

  return (
    <Stack gap="lg">
      <AuthSection onCancelAuth={handleCancelAuth} onLogout={handleLogout} />
      <ServerSection
        isAuthenticated={isAuthenticated}
        servers={servers}
        error={serversError}
        selectedServer={form.values.selectedServer}
        isSelecting={form.values.isSelecting}
        isSaved={form.values.isSaved}
        onFetchServers={refetchServers}
        onServerSelect={handleServerSelect}
        onSelectedServerChange={(server: Plex.Server | null) =>
          form.setFieldValue("selectedServer", server)
        }
      />
    </Stack>
  );
};

export default PlexSettings;
