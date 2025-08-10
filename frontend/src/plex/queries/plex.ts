import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";
import { parseAxiosError } from "@/plex/utilities/errors";

// Types - re-export from the API for consistency
export type {
  PlexPinResponse,
  PlexValidateResponse,
  PlexPinCheckResponse,
  PlexServerConnection,
  PlexServer,
  PlexServersResponse,
} from "@/apis/raw/plex";

// Auth validation query hook
export const usePlexAuthValidationQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "auth", "validate"],
    queryFn: async () => {
      try {
        return await api.plex.validateAuth();
      } catch (error) {
        // Handle Plex auth errors gracefully - return a safe state instead of throwing
        // This prevents Plex auth failures from triggering global logout
        const plexError = parseAxiosError(error);
        return {
          valid: false,
          error: plexError.message,
          code: plexError.code,
        };
      }
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    throwOnError: false, // Never throw errors from this query
  });
};

// Servers query hook
export const usePlexServersQuery = (enabled: boolean = true) => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "servers"],
    queryFn: async () => {
      try {
        return await api.plex.getServers();
      } catch (error) {
        const plexError = parseAxiosError(error);
        throw new Error(plexError.message);
      }
    },
    enabled,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
};

// Selected server query hook
export const usePlexSelectedServerQuery = (enabled: boolean = true) => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "selectedServer"],
    queryFn: async () => {
      try {
        return await api.plex.getSelectedServer();
      } catch (error) {
        // Return null instead of throwing for "no selected server" case
        return null;
      }
    },
    enabled,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

// PIN creation mutation
export const usePlexPinMutation = () => {
  return useMutation({
    mutationFn: async () => {
      try {
        return await api.plex.createPin();
      } catch (error) {
        const plexError = parseAxiosError(error);
        throw new Error(plexError.message);
      }
    },
  });
};

// PIN check mutation
export const usePlexPinCheckMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (pinId: string) => {
      try {
        return await api.plex.checkPin(pinId);
      } catch (error) {
        const plexError = parseAxiosError(error);
        throw new Error(plexError.message);
      }
    },
    onSuccess: (data: { authenticated: boolean }) => {
      if (data.authenticated) {
        // Invalidate auth validation query when authentication succeeds
        queryClient.invalidateQueries({
          queryKey: [QueryKeys.Plex, "auth", "validate"],
        });
      }
    },
  });
};

// Logout mutation
export const usePlexLogoutMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      try {
        await api.plex.logout();
      } catch (error) {
        const plexError = parseAxiosError(error);
        throw new Error(plexError.message);
      }
    },
    onSuccess: () => {
      // Invalidate all Plex queries on logout
      queryClient.invalidateQueries({
        queryKey: [QueryKeys.Plex],
      });
      // Also invalidate system queries as settings may have changed
      queryClient.invalidateQueries({
        queryKey: [QueryKeys.System],
      });
    },
  });
};

// Server selection mutation
export const usePlexServerSelectionMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      machineIdentifier: string;
      name: string;
      uri: string;
      local: boolean;
    }) => {
      try {
        return await api.plex.selectServer({
          machineIdentifier: params.machineIdentifier,
          name: params.name,
          connection: {
            uri: params.uri,
            local: params.local,
          },
        });
      } catch (error) {
        const plexError = parseAxiosError(error);
        throw new Error(plexError.message);
      }
    },
    onSuccess: () => {
      // Invalidate selected server query when selection changes
      queryClient.invalidateQueries({
        queryKey: [QueryKeys.Plex, "selectedServer"],
      });
      // Also invalidate system queries as settings may have changed
      queryClient.invalidateQueries({
        queryKey: [QueryKeys.System],
      });
    },
  });
};

// Connection test mutation
export const usePlexConnectionTestMutation = () => {
  return useMutation({
    mutationFn: async (uri: string) => {
      try {
        const startTime = Date.now();
        const result = await api.plex.testConnection(uri);
        const latency = Date.now() - startTime;
        return { ...result, latency };
      } catch (error) {
        return { success: false, latency: undefined };
      }
    },
  });
};
