import {
  useMutation,
  useQuery,
  useQueryClient,
  UseQueryOptions,
} from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

export const usePlexAuthValidationQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "auth", "validate"],
    queryFn: async () => {
      try {
        const result = await api.plex.validateAuth();
        return result;
      } catch (error) {
        // Return a default value when API is not available
        return {
          valid: false,
          // eslint-disable-next-line camelcase
          auth_method: "oauth",
          error: "API unavailable",
        };
      }
    },
    staleTime: 1000 * 60 * 5,
    throwOnError: false,
    retry: 1,
  });
};

export const usePlexServersQuery = <TData = Plex.Server[]>(
  options?: Partial<
    UseQueryOptions<Plex.Server[], Error, TData, (string | boolean)[]>
  > & { enabled?: boolean },
) => {
  const enabled = options?.enabled ?? true;

  return useQuery({
    queryKey: [QueryKeys.Plex, "servers"],
    queryFn: () => api.plex.servers(),
    enabled,
    staleTime: 1000 * 60 * 2,
    ...options,
  });
};

export const usePlexSelectedServerQuery = <TData = Plex.Server>(
  options?: Partial<
    UseQueryOptions<Plex.Server, Error, TData, (string | boolean)[]>
  > & { enabled?: boolean },
) => {
  const enabled = options?.enabled ?? true;

  return useQuery({
    queryKey: [QueryKeys.Plex, "selectedServer"],
    queryFn: () => api.plex.selectedServer(),
    enabled,
    staleTime: 1000 * 60 * 5,
    ...options,
  });
};

export const usePlexPinMutation = () => {
  return useMutation({
    mutationFn: () => api.plex.createPin(),
  });
};

export const usePlexPinCheckQuery = (
  pinId: string | null,
  enabled: boolean,
  refetchInterval: number | false,
) => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "pinCheck", pinId],
    queryFn: () => {
      if (!pinId) throw new Error("Pin ID is required");
      return api.plex.checkPin(pinId);
    },
    enabled: enabled && !!pinId,
    retry: false,
    refetchInterval: refetchInterval,
    refetchOnWindowFocus: false,
    staleTime: 0, // Always fresh for polling
  });
};

export const usePlexLogoutMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.plex.logout(),
    onSuccess: () => {
      // Remove all Plex queries from cache to prevent any refetch attempts after logout
      // This is intentional - on logout we want to completely clear Plex state
      queryClient.removeQueries({
        queryKey: [QueryKeys.Plex],
      });

      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.System],
      });
    },
  });
};

export const usePlexServerSelectionMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: {
      machineIdentifier: string;
      name: string;
      uri: string;
      local: boolean;
      connections?: string[];
    }) =>
      api.plex.selectServer({
        machineIdentifier: params.machineIdentifier,
        name: params.name,
        uri: params.uri,
        local: params.local,
        connections: params.connections,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.Plex, "selectedServer"],
      });
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.Plex, "libraries"],
      });
    },
  });
};

export const usePlexLibrariesQuery = <TData = Plex.Library[]>(
  options?: Partial<
    UseQueryOptions<Plex.Library[], Error, TData, (string | boolean)[]>
  > & { enabled?: boolean },
) => {
  const enabled = options?.enabled ?? true;

  return useQuery({
    queryKey: [QueryKeys.Plex, "libraries"],
    queryFn: () => api.plex.libraries(),
    enabled,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
    refetchOnWindowFocus: false, // Don't refetch on window focus
    retry: 3, // Retry failed requests 3 times
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff: 1s, 2s, 4s, max 30s
    ...options,
  });
};

export const usePlexWebhookCreateMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.plex.createWebhook(),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.Plex, "webhooks"],
      });
    },
  });
};

export const usePlexWebhookListQuery = <TData = Plex.WebhookList>(
  options?: Partial<
    UseQueryOptions<Plex.WebhookList, Error, TData, (string | boolean)[]>
  > & { enabled?: boolean },
) => {
  const enabled = options?.enabled ?? true;

  return useQuery({
    queryKey: [QueryKeys.Plex, "webhooks"],
    queryFn: () => api.plex.listWebhooks(),
    enabled,
    staleTime: 1000 * 60 * 2, // Cache for 2 minutes
    refetchOnWindowFocus: false,
    ...options,
  });
};

export const usePlexWebhookDeleteMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (webhookUrl: string) => api.plex.deleteWebhook(webhookUrl),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [QueryKeys.Plex, "webhooks"],
      });
    },
  });
};

export const usePlexAutopulseConfigQuery = <TData = Plex.AutopulseConfig>(
  options?: Partial<
    UseQueryOptions<Plex.AutopulseConfig, Error, TData, (string | boolean)[]>
  > & { enabled?: boolean },
) => {
  const enabled = options?.enabled ?? true;

  return useQuery({
    queryKey: [QueryKeys.Plex, "autopulse", "config"],
    queryFn: () => api.plex.getAutopulseConfig(),
    enabled,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
    refetchOnWindowFocus: false,
    throwOnError: false,
    retry: 1,
    ...options,
  });
};
