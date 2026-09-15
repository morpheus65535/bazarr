import { useMemo } from "react";
import { showNotification } from "@mantine/notifications";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";
import { notification } from "@/modules/task";
import { RouterNames } from "@/Router/RouterNames";
import { Environment } from "@/utilities";
import { setAuthenticated } from "@/utilities/event";

export const useBadges = () =>
  useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Badges],
    queryFn: () => api.badges.all(),
    refetchOnWindowFocus: "always",
    refetchInterval: 1000 * 60,
    staleTime: 1000 * 10,
  });

export const useFileSystem = (
  type: "bazarr" | "sonarr" | "radarr",
  path: string,
  enabled: boolean,
) =>
  useQuery({
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

export const useSystemSettings = () =>
  useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Settings],
    queryFn: () => api.system.settings(),
    staleTime: Infinity,
  });

export const useSystemJobs = () =>
  useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Jobs],
    queryFn: () => api.system.jobs(),
    staleTime: 30_000,
    refetchOnWindowFocus: true,
    refetchInterval: (query) => {
      const hasRunning = query.state.data?.some((j) => j.status === "running");
      return hasRunning ? 10_000 : false;
    },
  });

export const useSettingsMutation = (options?: { silent?: boolean }) => {
  const client = useQueryClient();
  const silent = options?.silent ?? false;
  return useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Settings],
    mutationFn: (data: Record<string, unknown>) =>
      api.system.updateSettings(data),

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

      if (!silent) {
        showNotification(
          notification.info("Settings saved", "Your changes have been saved"),
        );
      }
    },

    onError: () => {
      showNotification(
        notification.error(
          "Save failed",
          "An error occurred while saving settings",
        ),
      );
    },
  });
};

export const useServerSearch = (query: string, enabled: boolean) =>
  useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Search, query],
    queryFn: () => api.system.search(query),
    enabled,
  });

export const useSystemLogs = () =>
  useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Logs],
    queryFn: () => api.system.logs(),
    refetchOnWindowFocus: "always",
    refetchInterval: 1000 * 60,
    staleTime: 1000 * 10,
  });

export const useDeleteLogs = () => {
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
};

export const useSystemAnnouncements = () =>
  useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Announcements],
    queryFn: () => api.system.announcements(),
    refetchOnWindowFocus: "always",
    refetchInterval: 1000 * 60,
    staleTime: 1000 * 10,
  });

export const useSystemAnnouncementsAddDismiss = () => {
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
};

export const useSystemTasks = () =>
  useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Tasks],
    queryFn: () => api.system.tasks(),
    refetchOnWindowFocus: "always",
    refetchInterval: 1000 * 60,
    staleTime: 1000 * 10,
  });

export const useRunTask = () => {
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
};

export const useSystemBackups = () =>
  useQuery({
    queryKey: [QueryKeys.System, "backups"],
    queryFn: () => api.system.backups(),
  });

export const useCreateBackups = () => {
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
};

export const useRestoreBackups = () => {
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
};

export const useDeleteBackups = () => {
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
};

export const useSystemStatus = () =>
  useQuery({
    queryKey: [QueryKeys.System, "status"],
    queryFn: () => api.system.status(),
  });

export const useSystemHealth = () =>
  useQuery({
    queryKey: [QueryKeys.System, "health"],
    queryFn: () => api.system.health(),
  });

export const useSystemReleases = () =>
  useQuery({
    queryKey: [QueryKeys.System, "releases"],
    queryFn: () => api.system.releases(),
  });

export const useSystem = () => {
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
      const params = new URLSearchParams(window.location.search);
      const returnTo = params.get("returnTo");
      const safeReturnTo =
        returnTo &&
        returnTo.startsWith("/") &&
        !returnTo.startsWith("//") &&
        returnTo !== RouterNames.Auth
          ? returnTo
          : undefined;

      const redirectUrl = safeReturnTo
        ? `${Environment.baseUrl}${safeReturnTo}`
        : Environment.baseUrl;

      window.location.replace(redirectUrl);
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
      isLoggingIn,
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
};

export const useSystemWebhookTestMutation = () =>
  useMutation({
    mutationFn: () => api.system.testWebhook(),
  });
