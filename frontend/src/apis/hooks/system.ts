import { useQuery } from "react-query";
import { SystemApi } from "..";

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
