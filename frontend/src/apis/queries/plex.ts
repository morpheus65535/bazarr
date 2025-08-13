import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

export type {
  PlexPinResponse,
  PlexValidateResponse,
  PlexPinCheckResponse,
  PlexServerConnection,
  PlexServer,
  PlexServersResponse,
} from "@/apis/raw/plex";

export const usePlexAuthValidationQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "auth", "validate"],
    queryFn: () => api.plex.validateAuth(),
    staleTime: 1000 * 60 * 5,
    throwOnError: false,
  });
};

export const usePlexServersQuery = (enabled: boolean = true) => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "servers"],
    queryFn: () => api.plex.getServers(),
    enabled,
    staleTime: 1000 * 60 * 2,
  });
};

export const usePlexSelectedServerQuery = (enabled: boolean = true) => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "selectedServer"],
    queryFn: () => api.plex.getSelectedServer(),
    enabled,
    staleTime: 1000 * 60 * 5,
  });
};

export const usePlexPinMutation = () => {
  return useMutation({
    mutationFn: () => api.plex.createPin(),
  });
};

export const usePlexPinCheckMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (pinId: string) => api.plex.checkPin(pinId),
    onSuccess: (data: { authenticated: boolean }) => {
      if (data.authenticated) {
        queryClient.invalidateQueries({
          queryKey: [QueryKeys.Plex, "auth", "validate"],
        });
      }
    },
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
