import { useMutation, useQuery } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";
import { PlexServer } from "@/apis/raw/plex";

export function usePlexServers() {
  return useQuery({
    queryKey: [QueryKeys.System, "plex", "servers"],
    queryFn: () => api.plex.getServers(),
    retry: false,
  });
}

export function usePlexOAuth() {
  return useMutation({
    mutationFn: () => api.plex.startOAuth(),
  });
}

export function usePlexSelectServer() {
  return useMutation({
    mutationFn: (server: Partial<PlexServer>) => api.plex.selectServer(server),
  });
}
