import { useQuery } from "react-query";
import QueryKeys from "../queries/keys";
import api from "../raw";

export function useSystemSettings() {
  return useQuery([QueryKeys.system, QueryKeys.settings], () =>
    api.system.settings()
  );
}

export function useLanguages(history?: boolean) {
  return useQuery(
    [QueryKeys.system, QueryKeys.settings, QueryKeys.languages, history],
    () => api.system.languages(history)
  );
}

export function useLanguageProfiles() {
  return useQuery(
    [QueryKeys.system, QueryKeys.settings, QueryKeys.languagesProfiles],
    () => api.system.languagesProfileList()
  );
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
