import { useMutation, useQuery, useQueryClient } from "react-query";
import QueryKeys from "../queries/keys";
import api from "../raw";

export function useSystemSettings() {
  return useQuery(QueryKeys.settings, () => api.system.settings(), {
    keepPreviousData: true,
    staleTime: Infinity,
  });
}

export function useSettingsMutation() {
  const client = useQueryClient();
  return useMutation((data: LooseObject) => api.system.updateSettings(data), {
    onSuccess: () => {
      client.invalidateQueries(QueryKeys.settings);
      client.invalidateQueries(QueryKeys.languages);
      client.invalidateQueries(QueryKeys.languagesProfiles);
    },
  });
}

export function useLanguages(history?: boolean) {
  return useQuery(
    [QueryKeys.languages, history],
    () => api.system.languages(history),
    {
      keepPreviousData: true,
      staleTime: Infinity,
    }
  );
}

export function useLanguageProfiles() {
  return useQuery(
    QueryKeys.languagesProfiles,
    () => api.system.languagesProfileList(),
    {
      keepPreviousData: true,
      staleTime: Infinity,
    }
  );
}

export function useServerSearch(query: string) {
  return useQuery(["search", query], () => api.system.search(query), {
    keepPreviousData: true,
  });
}

export function useSystemLogs() {
  return useQuery(["logs"], () => api.system.logs());
}

export function useSystemTasks() {
  return useQuery(["tasks"], () => api.system.tasks());
}

export function useSystemStatus() {
  return useQuery(["status"], () => api.system.status());
}

export function useSystemHealth() {
  return useQuery(["health"], () => api.system.health());
}

export function useSystemProviders(history?: boolean) {
  return useQuery(["providers"], () => api.providers.providers(history));
}

export function useSystemReleases() {
  return useQuery(["releases"], () => api.system.releases());
}
