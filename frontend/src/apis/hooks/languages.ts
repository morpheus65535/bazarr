import { useQuery } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

export function useLanguages(history?: boolean) {
  return useQuery(
    [QueryKeys.System, QueryKeys.Languages, history ?? false],
    () => api.system.languages(history),
    {
      staleTime: Infinity,
    },
  );
}

export function useLanguageProfiles() {
  return useQuery(
    [QueryKeys.System, QueryKeys.LanguagesProfiles],
    () => api.system.languagesProfileList(),
    {
      staleTime: Infinity,
    },
  );
}
