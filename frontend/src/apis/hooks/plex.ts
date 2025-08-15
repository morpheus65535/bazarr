// Re-export React Query hooks directly - no custom hook logic
export {
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckQuery,
  usePlexPinMutation,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
  type PlexPinResponse,
  type PlexServer,
  type PlexServerConnection,
} from "@/apis/queries/plex";
