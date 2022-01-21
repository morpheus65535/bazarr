import { useQuery } from "react-query";
import QueryKeys from "../queries/keys";
import api from "../raw";

export function useLanguages(history?: boolean) {
  return useQuery(
    [QueryKeys.languages, history],
    () => api.system.languages(history),
    {
      staleTime: Infinity,
    }
  );
}

export function useLanguageProfiles() {
  return useQuery(
    QueryKeys.languagesProfiles,
    () => api.system.languagesProfileList(),
    {
      staleTime: Infinity,
    }
  );
}
