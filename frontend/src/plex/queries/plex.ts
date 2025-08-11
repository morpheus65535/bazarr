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

// Auth validation query hook with user-specific cache key
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
    staleTime: 1000 * 60 * 2, // Reduced to 2 minutes for faster auth state updates
    gcTime: 1000 * 60 * 5, // Keep in cache for 5 minutes
    throwOnError: false, // Never throw errors from this query
  });
};

// Servers query hook with user-specific cache key to prevent cross-user pollution
export const usePlexServersQuery = (
  userId?: string,
  enabled: boolean = true,
) => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "servers", userId || "anonymous"],
    queryFn: async () => {
      try {
        return await api.plex.getServers();
      } catch (error) {
        const plexError = parseAxiosError(error);
        throw new Error(plexError.message);
      }
    },
    enabled: enabled && !!userId,
    staleTime: 1000 * 60 * 1, // Reduced to 1 minute for faster updates
    gcTime: 1000 * 60 * 5, // Keep in cache for 5 minutes
  });
};

// Selected server query hook with user-specific cache key
export const usePlexSelectedServerQuery = (
  userId?: string,
  enabled: boolean = true,
) => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "selectedServer", userId || "anonymous"],
    queryFn: async () => {
      try {
        return await api.plex.getSelectedServer();
      } catch (error) {
        // Return null instead of throwing for "no selected server" case
        return null;
      }
    },
    enabled: enabled && !!userId,
    staleTime: 1000 * 60 * 2, // Reduced for faster updates
    gcTime: 1000 * 60 * 5,
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

// PIN check mutation with optimistic cache updates to eliminate lag
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
    onSuccess: (data: {
      authenticated: boolean;
      username?: string;
      email?: string;
    }) => {
      if (data.authenticated) {
        // Immediately invalidate auth validation query when authentication succeeds
        queryClient.invalidateQueries({
          queryKey: [QueryKeys.Plex, "auth", "validate"],
        });

        // Optimistically update the auth cache to eliminate 1-second lag
        queryClient.setQueryData([QueryKeys.Plex, "auth", "validate"], {
          valid: true,
          // eslint-disable-next-line camelcase
          auth_method: "oauth",
          username: data.username,
          email: data.email,
        });

        // Clear any old server caches since user context might have changed
        queryClient.removeQueries({
          queryKey: [QueryKeys.Plex, "servers"],
        });
        queryClient.removeQueries({
          queryKey: [QueryKeys.Plex, "selectedServer"],
        });
      }
    },
  });
};

// Logout mutation with complete cache cleanup
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
      // Complete cache cleanup on logout - fixes "wrong auth" bug
      queryClient.clear(); // Clear ALL cache to prevent stale auth states

      // Immediately set logged-out state
      queryClient.setQueryData([QueryKeys.Plex, "auth", "validate"], {
        valid: false,
        // eslint-disable-next-line camelcase
        auth_method: "apikey",
      });
    },
  });
};

// Server selection mutation with user-specific cache invalidation
export const usePlexServerSelectionMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      machineIdentifier: string;
      name: string;
      uri: string;
      local: boolean;
      userId?: string;
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
    onSuccess: (data, variables) => {
      // Invalidate user-specific selected server query when selection changes
      queryClient.invalidateQueries({
        queryKey: [
          QueryKeys.Plex,
          "selectedServer",
          variables.userId || "anonymous",
        ],
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
