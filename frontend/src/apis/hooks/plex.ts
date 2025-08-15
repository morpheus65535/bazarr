// Re-export React Query hooks directly - no custom hook logic
export {
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckQuery,
  usePlexPinMutation,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
} from "@/apis/queries/plex";

// Export types that we need for the components
export type PlexServer = {
  name: string;
  machineIdentifier: string;
  platform?: string;
  version?: string;
  connections: PlexServerConnection[];
  bestConnection?: PlexServerConnection;
};

export type PlexServerConnection = {
  uri: string;
  local: boolean;
  available?: boolean;
};

export type PlexPinResponse = {
  data: {
    pinId: string;
    code: string;
    authUrl: string;
  };
};
