import type { UseQueryOptions } from "@tanstack/react-query";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";
import type {
  PlexPinCheckResponse,
  PlexPinResponse,
  PlexSelectedServerResponse,
  PlexServer,
  PlexServerConnection,
  PlexServersResponse,
  PlexValidateResponse,
} from "@/apis/raw/plex";

export type {
  PlexPinResponse,
  PlexValidateResponse,
  PlexPinCheckResponse,
  PlexServerConnection,
  PlexServer,
  PlexServersResponse,
  PlexSelectedServerResponse,
};

export const usePlexAuthValidationQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "auth", "validate"],
    queryFn: () => api.plex.validateAuth(),
    staleTime: 1000 * 60 * 5,
    throwOnError: false,
  });
};

export const usePlexServersQuery = <TData = PlexServersResponse>(
  options?: Partial<
    UseQueryOptions<PlexServersResponse, Error, TData, (string | boolean)[]>
  > & { enabled?: boolean },
) => {
  const enabled = options?.enabled ?? true;

  return useQuery({
    queryKey: [QueryKeys.Plex, "servers"],
    queryFn: () => api.plex.getServers(),
    enabled,
    staleTime: 1000 * 60 * 2,
    ...options,
  });
};

export const usePlexSelectedServerQuery = <TData = PlexSelectedServerResponse>(
  options?: Partial<
    UseQueryOptions<
      PlexSelectedServerResponse,
      Error,
      TData,
      (string | boolean)[]
    >
  > & { enabled?: boolean },
) => {
  const enabled = options?.enabled ?? true;

  return useQuery({
    queryKey: [QueryKeys.Plex, "selectedServer"],
    queryFn: () => api.plex.getSelectedServer(),
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
  enabled: boolean = false,
) => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "pinCheck", pinId],
    queryFn: () => api.plex.checkPin(pinId!),
    enabled: enabled && !!pinId,
    refetchInterval: (data: PlexPinCheckResponse | undefined) => {
      // Stop polling if authenticated or error
      return data?.authenticated ? false : 2000;
    },
    refetchIntervalInBackground: false,
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 0,
  });
};

export const usePlexLogoutMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.plex.logout(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [QueryKeys.Plex],
      });
      queryClient.invalidateQueries({
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
    }) =>
      api.plex.selectServer({
        machineIdentifier: params.machineIdentifier,
        name: params.name,
        connection: {
          uri: params.uri,
          local: params.local,
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [QueryKeys.Plex, "selectedServer"],
      });
    },
  });
};
