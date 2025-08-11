import React, { useCallback, useContext, useEffect } from "react";
import { Stack } from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import { FormContext } from "@/pages/Settings/utilities/FormValues";
import { usePlexManagement } from "@/plex/hooks/usePlexManagement";
import type { PlexServer } from "@/plex/queries/plex";
import { PlexAuthSection } from "./PlexAuthSection";
import { PlexServerSection } from "./PlexServerSection";

export const PlexSettings: React.FC = () => {
  const queryClient = useQueryClient();
  const form = useContext(FormContext);

  // Use consolidated Plex management hook
  const plex = usePlexManagement({
    onAuthSuccess: () => {
      // Invalidate form cache on successful auth
      queryClient.invalidateQueries({ queryKey: [QueryKeys.System] });

      // Reset form properly using Promise microtask to avoid race conditions
      if (form) {
        Promise.resolve().then(() => {
          form.reset();
        });
      }
    },
  });

  // Centralized server selection effect - handles all server selection logic
  useEffect(() => {
    if (!plex.auth.isAuthenticated) return;

    // Priority 1: Use saved server from API
    if (plex.servers.selected && !plex.selection.isSaved) {
      plex.selection.setSelectedServer(plex.servers.selected);
      plex.selection.setSelectedServerId(
        plex.servers.selected.machineIdentifier,
      );
      plex.selection.setSaved(true);
      return;
    }

    // Priority 2: Auto-select single available server
    if (
      plex.servers.list.length === 1 &&
      plex.servers.list[0].bestConnection &&
      !plex.selection.isSaved &&
      !plex.servers.selected
    ) {
      const singleServer = plex.servers.list[0];
      plex.selection.setSelectedServerId(singleServer.machineIdentifier);

      // Auto-select the single server
      plex.servers
        .selectServer(singleServer.machineIdentifier)
        .then(() => {
          plex.selection.setSelectedServer(singleServer);
          plex.selection.setSaved(true);
        })
        .catch(() => {
          // Error is handled by the selectServer mutation
        });
    }
  }, [plex]);

  // Fetch servers with connection testing when authenticated
  useEffect(() => {
    if (plex.auth.isAuthenticated && plex.servers.list.length > 0) {
      plex.servers.fetchServers();
    }
  }, [plex]);

  // Handle server selection
  const handleServerSelect = useCallback(async () => {
    if (!plex.selection.selectedServerId) return;

    plex.selection.setSelecting(true);
    try {
      const server = plex.servers.list.find(
        (s: PlexServer) =>
          s.machineIdentifier === plex.selection.selectedServerId,
      );

      if (server?.bestConnection) {
        await plex.servers.selectServer(plex.selection.selectedServerId);
        plex.selection.setSelectedServer(server);
        plex.selection.setSaved(true);
      }
    } catch {
      // Error is handled by the hook
    } finally {
      plex.selection.setSelecting(false);
    }
  }, [plex]);

  // Handle logout
  const handleLogout = useCallback(async () => {
    await plex.auth.logout();

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
  }, [plex, queryClient, form]);

  return (
    <Stack gap="lg">
      <PlexAuthSection
        isLoading={plex.auth.isLoading}
        isPolling={plex.auth.isPolling}
        isAuthenticated={plex.auth.isAuthenticated}
        pinData={plex.auth.pinData}
        authError={plex.auth.error}
        username={plex.auth.username}
        email={plex.auth.email}
        onStartAuth={plex.auth.startAuth}
        onCancelAuth={plex.auth.cancelAuth}
        onLogout={handleLogout}
      />
      <PlexServerSection
        isAuthenticated={plex.auth.isAuthenticated}
        servers={plex.servers.list}
        isLoading={plex.servers.isLoading}
        error={plex.servers.error}
        selectedServerId={plex.selection.selectedServerId}
        selectedServer={plex.selection.selectedServer}
        isSelecting={plex.selection.isSelecting}
        isSaved={plex.selection.isSaved}
        onFetchServers={plex.servers.fetchServers}
        onServerSelect={handleServerSelect}
        onSelectedServerIdChange={plex.selection.setSelectedServerId}
      />
    </Stack>
  );
};

export default PlexSettings;
