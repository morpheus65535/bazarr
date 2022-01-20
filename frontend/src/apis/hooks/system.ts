import { useQuery } from "react-query";
import { ProvidersApi, SystemApi } from "..";

export function useSystemSettings() {
  return useQuery(["system", "settings"], () => SystemApi.settings());
}

export function useLanguages(history?: boolean) {
  return useQuery(["system", "settings", "languages", history], () =>
    SystemApi.languages(history)
  );
}

export function useLanguageProfiles() {
  return useQuery(["system", "settings", "languages", "profiles"], () =>
    SystemApi.languagesProfileList()
  );
}

export function useSystemLogs() {
  return useQuery(["logs"], () => SystemApi.logs());
}

export function useSystemTasks() {
  return useQuery(["tasks"], () => SystemApi.tasks());
}

export function useSystemStatus() {
  return useQuery(["status"], () => SystemApi.status());
}

export function useSystemHealth() {
  return useQuery(["health"], () => SystemApi.health());
}

export function useSystemProviders(history?: boolean) {
  return useQuery(["providers"], () => ProvidersApi.providers(history));
}

export function useSystemReleases() {
  return useQuery(["releases"], () => SystemApi.releases());
}
