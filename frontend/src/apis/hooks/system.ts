import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { siteRedirectToAuth } from "../../@redux/actions";
import store from "../../@redux/store";
import QueryKeys from "../queries/keys";
import api from "../raw";

export function useBadges() {
  return useQuery(QueryKeys.badges, () => api.badges.all());
}

export function useSystemSettings() {
  return useQuery(QueryKeys.settings, () => api.system.settings(), {
    staleTime: Infinity,
  });
}

export function useSettingsMutation() {
  const client = useQueryClient();
  return useMutation((data: LooseObject) => api.system.updateSettings(data), {
    onSuccess: () => {
      client.invalidateQueries([
        QueryKeys.settings,
        QueryKeys.settings,
        QueryKeys.languagesProfiles,
      ]);
    },
  });
}

export function useServerSearch(query: string) {
  return useQuery(["search", query], () => api.system.search(query));
}

export function useSystemLogs() {
  return useQuery("logs", () => api.system.logs());
}

export function useDeleteLogs() {
  const client = useQueryClient();
  return useMutation(() => api.system.deleteLogs(), {
    onSuccess: () => {
      client.invalidateQueries("logs");
    },
  });
}

export function useSystemTasks() {
  return useQuery("tasks", () => api.system.tasks());
}

export function useSystemStatus() {
  return useQuery("status", () => api.system.status());
}

export function useSystemHealth() {
  return useQuery("health", () => api.system.health());
}

export function useSystemProviders(history?: boolean) {
  return useQuery("providers", () => api.providers.providers(history));
}

export function useSystemReleases() {
  return useQuery("releases", () => api.system.releases());
}

export function useSystem() {
  const { mutate: logout, isLoading: isLoggingOut } = useMutation(
    () => api.system.logout(),
    {
      onSuccess: () => {
        store.dispatch(siteRedirectToAuth());
      },
    }
  );

  const { mutate: shutdown, isLoading: isShuttingDown } = useMutation(
    () => api.system.shutdown(),
    {
      onSuccess: () => {},
    }
  );

  const { mutate: restart, isLoading: isRestarting } = useMutation(
    () => api.system.restart(),
    {}
  );

  return useMemo(
    () => ({
      logout,
      shutdown,
      restart,
      isWorking: isLoggingOut || isShuttingDown || isRestarting,
    }),
    [isLoggingOut, isRestarting, isShuttingDown, logout, restart, shutdown]
  );
}
