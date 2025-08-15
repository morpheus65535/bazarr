import { useCallback, useEffect } from "react";
import { Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
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

  // Extract stable form methods to satisfy ESLint exhaustive-deps
  // const { setFieldValue, values, reset } = serverForm;

  const { setValue } = useFormActions();

  // const {
  //   servers,
  //   selectedServer: savedSelectedServer,
  //   error: serversError,
  //   selectServer,
  //   refetchServers,
  // } = usePlexServers();
  //
  // // Plex OAuth hook (React Query version)
  // const {
  //   isAuthenticated,
  //   isLoading: authLoading,
  //   username,
  //   email,
  //   error: authError,
  //   pinData,
  //   isPolling,
  //   startAuth,
  //   cancelAuth,
  // } = usePlexOAuth({
  //   onAuthSuccess: () => {
  //     // Just refetch servers on auth success - useEffect handles the rest
  //     refetchServers();
  //   },
  // });
  //
  // const performAutoSelection = useCallback(
  //   async (server: Plex.Server) => {
  //     setFieldValue("selectedServer", server);
  //     setFieldValue("isSelecting", true);
  //
  //     try {
  //       await selectServer(server.machineIdentifier);
  //       setFieldValue("isSaved", true);
  //     } catch {
  //       // Error is handled by the selectServer mutation
  //     } finally {
  //       setFieldValue("isSelecting", false);
  //     }
  //   },
  //   [setFieldValue, selectServer],
  // );
  //
  // const handleSavedServerSelection = useCallback(
  //   (server: Plex.Server) => {
  //     setFieldValue("selectedServer", server);
  //     setFieldValue("isSaved", true);
  //   },
  //   [setFieldValue],
  // );
  //
  // const isSaved = values.isSaved;
  //
  // useEffect(() => {
  //   if (!isAuthenticated) {
  //     return;
  //   }
  //
  //   if (savedSelectedServer && !isSaved) {
  //     handleSavedServerSelection(savedSelectedServer);
  //     return;
  //   }
  //
  //   if (
  //     servers.length === 1 &&
  //     servers[0].bestConnection &&
  //     !isSaved &&
  //     !savedSelectedServer
  //   ) {
  //     const singleServer = servers[0];
  //     performAutoSelection(singleServer);
  //   }
  // }, [
  //   isAuthenticated,
  //   servers,
  //   savedSelectedServer,
  //   isSaved,
  //   performAutoSelection,
  //   handleSavedServerSelection,
  // ]);
  //
  // const handleServerSelect = useCallback(async () => {
  //   const selectedServer = values.selectedServer;
  //   if (!selectedServer) return;
  //
  //   setFieldValue("isSelecting", true);
  //   try {
  //     if (selectedServer.bestConnection) {
  //       await selectServer(selectedServer.machineIdentifier);
  //       setFieldValue("isSaved", true);
  //     }
  //   } catch {
  //     // Error is handled by the hook
  //   } finally {
  //     setFieldValue("isSelecting", false);
  //   }
  // }, [values.selectedServer, setFieldValue, selectServer]);

  const handleLogout = () => {
    form.reset();
  };

  return (
    <Stack gap="lg">
      <AuthSection onCancelAuth={handleCancelAuth} onLogout={handleLogout} />
      <ServerSection
        isAuthenticated={isAuthenticated}
        servers={servers}
        error={serversError}
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
