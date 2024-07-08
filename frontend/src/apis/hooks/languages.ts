import { useQuery } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

export function useLanguages(history?: boolean) {
  return useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Languages, history ?? false],
    queryFn: () => api.system.languages(history),
    staleTime: Infinity,
  });
}

export function useLanguageProfiles() {
  return useQuery({
    queryKey: [QueryKeys.System, QueryKeys.LanguagesProfiles],
    queryFn: () => api.system.languagesProfileList(),
    staleTime: Infinity,
  });
}
