import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { setUnauthenticated } from "../../modules/redux/actions";
import store from "../../modules/redux/store";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useBadges() {
  return useQuery([QueryKeys.System, QueryKeys.Badges], () => api.badges.all());
}

export function useFileSystem(
  type: "bazarr" | "sonarr" | "radarr",
  path: string,
  enabled: boolean
) {
  return useQuery(
    [QueryKeys.FileSystem, type, path],
    () => {
      if (type === "bazarr") {
        return api.files.bazarr(path);
      } else if (type === "radarr") {
        return api.files.radarr(path);
      } else if (type === "sonarr") {
        return api.files.sonarr(path);
      }
    },
    {
      enabled,
    }
  );
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

export function useServerSearch(query: string, enabled: boolean) {
  return useQuery(
    [QueryKeys.System, QueryKeys.Search, query],
    () => api.system.search(query),
    {
      enabled,
    }
  );
}

export function useSystemLogs() {
  return useQuery([QueryKeys.System, QueryKeys.Logs], () => api.system.logs(), {
    refetchOnWindowFocus: "always",
    refetchInterval: 1000 * 60,
    staleTime: 1000,
  });
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
  return useQuery(
    [QueryKeys.System, QueryKeys.Tasks],
    () => api.system.tasks(),
    {
      refetchOnWindowFocus: "always",
      refetchInterval: 1000 * 60,
      staleTime: 1000 * 10,
    }
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
        client.invalidateQueries([QueryKeys.System, QueryKeys.Backups]);
      },
    }
  );
}

export function useSystemBackups() {
  return useQuery([QueryKeys.System, "backups"], () => api.system.backups());
}

export function useCreateBackups() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.System, QueryKeys.Backups],
    () => api.system.createBackups(),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.System, QueryKeys.Backups]);
      },
    }
  );
}

export function useRestoreBackups() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.System, QueryKeys.Backups],
    (filename: string) => api.system.restoreBackups(filename),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.System, QueryKeys.Backups]);
      },
    }
  );
}

export function useDeleteBackups() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.System, QueryKeys.Backups],
    (filename: string) => api.system.deleteBackups(filename),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.System, QueryKeys.Backups]);
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
        store.dispatch(setUnauthenticated());
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
      isMutating: isLoggingOut || isShuttingDown || isRestarting || isLoggingIn,
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
