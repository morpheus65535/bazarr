import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";
import { Environment } from "@/utilities";
import { setAuthenticated } from "@/utilities/event";

export function useBadges() {
  return useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Badges],
    queryFn: () => api.badges.all(),
    refetchOnWindowFocus: "always",
    refetchInterval: 1000 * 60,
    staleTime: 1000 * 10,
  });
}

export function useFileSystem(
  type: "bazarr" | "sonarr" | "radarr",
  path: string,
  enabled: boolean,
) {
  return useQuery({
    queryKey: [QueryKeys.FileSystem, type, path],

    queryFn: () => {
      if (type === "bazarr") {
        return api.files.bazarr(path);
      } else if (type === "radarr") {
        return api.files.radarr(path);
      } else if (type === "sonarr") {
        return api.files.sonarr(path);
      }

      return [];
    },

    enabled,
  });
}

export function useSystemSettings() {
  return useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Settings],
    queryFn: () => api.system.settings(),
    staleTime: Infinity,
  });
}

export function useSettingsMutation() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Settings],
    mutationFn: (data: LooseObject) => api.system.updateSettings(data),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.Series],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.Episodes],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.Movies],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.Wanted],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.Badges],
      });

      // Invalidate Plex libraries when settings change (e.g., server configuration)
      void client.invalidateQueries({
        queryKey: [QueryKeys.Plex, "libraries"],
      });
    },
  });
}

export function useServerSearch(query: string, enabled: boolean) {
  return useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Search, query],
    queryFn: () => api.system.search(query),
    enabled,
  });
}

export function useSystemLogs() {
  return useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Logs],
    queryFn: () => api.system.logs(),
    refetchOnWindowFocus: "always",
    refetchInterval: 1000 * 60,
    staleTime: 1000 * 10,
  });
}

export function useDeleteLogs() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Logs],
    mutationFn: () => api.system.deleteLogs(),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Logs],
      });
    },
  });
}

export function useSystemAnnouncements() {
  return useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Announcements],
    queryFn: () => api.system.announcements(),
    refetchOnWindowFocus: "always",
    refetchInterval: 1000 * 60,
    staleTime: 1000 * 10,
  });
}

export function useSystemAnnouncementsAddDismiss() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Announcements],

    mutationFn: (param: { hash: string }) => {
      const { hash } = param;
      return api.system.addAnnouncementsDismiss(hash);
    },

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Announcements],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Badges],
      });
    },
  });
}

export function useSystemTasks() {
  return useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Tasks],
    queryFn: () => api.system.tasks(),
    refetchOnWindowFocus: "always",
    refetchInterval: 1000 * 60,
    staleTime: 1000 * 10,
  });
}

export function useRunTask() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Tasks],
    mutationFn: (id: string) => api.system.runTask(id),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Tasks],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Backups],
      });
    },
  });
}

export function useSystemBackups() {
  return useQuery({
    queryKey: [QueryKeys.System, "backups"],
    queryFn: () => api.system.backups(),
  });
}

export function useCreateBackups() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Backups],
    mutationFn: () => api.system.createBackups(),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Backups],
      });
    },
  });
}

export function useRestoreBackups() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Backups],
    mutationFn: (filename: string) => api.system.restoreBackups(filename),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Backups],
      });
    },
  });
}

export function useDeleteBackups() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Backups],
    mutationFn: (filename: string) => api.system.deleteBackups(filename),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Backups],
      });
    },
  });
}

export function useSystemStatus() {
  return useQuery({
    queryKey: [QueryKeys.System, "status"],
    queryFn: () => api.system.status(),
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: [QueryKeys.System, "health"],
    queryFn: () => api.system.health(),
  });
}

export function useSystemReleases() {
  return useQuery({
    queryKey: [QueryKeys.System, "releases"],
    queryFn: () => api.system.releases(),
  });
}

export function useSystem() {
  const client = useQueryClient();
  const { mutate: logout, isPending: isLoggingOut } = useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Actions],
    mutationFn: () => api.system.logout(),

    onSuccess: () => {
      setAuthenticated(false);
      client.clear();
    },
  });

  const { mutate: login, isPending: isLoggingIn } = useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Actions],

    mutationFn: (param: { username: string; password: string }) =>
      api.system.login(param.username, param.password),

    onSuccess: () => {
      // TODO: Hard-coded value
      window.location.replace(Environment.baseUrl);
    },
  });

  const { mutate: shutdown, isPending: isShuttingDown } = useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Actions],
    mutationFn: () => api.system.shutdown(),

    onSuccess: () => {
      client.clear();
    },
  });

  const { mutate: restart, isPending: isRestarting } = useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Actions],
    mutationFn: () => api.system.restart(),

    onSuccess: () => {
      client.clear();
    },
  });

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
    ],
  );
}

export function useSystemWebhookTestMutation() {
  return useMutation({
    mutationFn: () => api.system.testWebhook(),
  });
}
