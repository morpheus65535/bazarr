import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { siteRedirectToAuth } from "../../@redux/actions";
import store from "../../@redux/store";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useBadges() {
  return useQuery([QueryKeys.System, QueryKeys.Badges], () => api.badges.all());
}

export function useSystemSettings() {
  return useQuery(
    [QueryKeys.System, QueryKeys.Settings],
    () => api.system.settings(),
    {
      staleTime: Infinity,
    }
  );
}

export function useSettingsMutation() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.System, QueryKeys.Settings],
    (data: LooseObject) => api.system.updateSettings(data),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.System]);
      },
    }
  );
}

export function useServerSearch(query: string) {
  return useQuery([QueryKeys.System, QueryKeys.Search, query], () =>
    query.length > 0 ? api.system.search(query) : null
  );
}

export function useSystemLogs() {
  return useQuery([QueryKeys.System, QueryKeys.Logs], () => api.system.logs());
}

export function useDeleteLogs() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.System, QueryKeys.Logs],
    () => api.system.deleteLogs(),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.System, QueryKeys.Logs]);
      },
    }
  );
}

export function useSystemTasks() {
  return useQuery([QueryKeys.System, QueryKeys.Tasks], () =>
    api.system.tasks()
  );
}

export function useRunTask() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.System, QueryKeys.Tasks],
    (id: string) => api.system.runTask(id),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.System, QueryKeys.Tasks]);
      },
    }
  );
}

export function useSystemStatus() {
  return useQuery([QueryKeys.System, "status"], () => api.system.status());
}

export function useSystemHealth() {
  return useQuery([QueryKeys.System, "health"], () => api.system.health());
}

export function useSystemReleases() {
  return useQuery([QueryKeys.System, "releases"], () => api.system.releases());
}

export function useSystem() {
  const client = useQueryClient();
  const { mutate: logout, isLoading: isLoggingOut } = useMutation(
    [QueryKeys.System, QueryKeys.Actions],
    () => api.system.logout(),
    {
      onSuccess: () => {
        store.dispatch(siteRedirectToAuth());
        client.clear();
      },
    }
  );

  const { mutate: login, isLoading: isLoggingIn } = useMutation(
    [QueryKeys.System, QueryKeys.Actions],
    (param: { username: string; password: string }) =>
      api.system.login(param.username, param.password),
    {
      onSuccess: () => {
        window.location.reload();
      },
    }
  );

  const { mutate: shutdown, isLoading: isShuttingDown } = useMutation(
    [QueryKeys.System, QueryKeys.Actions],
    () => api.system.shutdown(),
    {
      onSuccess: () => {
        client.clear();
      },
    }
  );

  const { mutate: restart, isLoading: isRestarting } = useMutation(
    [QueryKeys.System, QueryKeys.Actions],
    () => api.system.restart(),
    {
      onSuccess: () => {
        client.clear();
      },
    }
  );

  return useMemo(
    () => ({
      logout,
      shutdown,
      restart,
      login,
      isWorking: isLoggingOut || isShuttingDown || isRestarting || isLoggingIn,
    }),
    [
      isLoggingIn,
      isLoggingOut,
      isRestarting,
      isShuttingDown,
      login,
      logout,
      restart,
      shutdown,
    ]
  );
}
