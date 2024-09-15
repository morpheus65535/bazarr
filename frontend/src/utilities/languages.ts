import { useMemo } from "react";
import { useLanguageProfiles, useLanguages } from "@/apis/hooks";

export function useLanguageProfileBy(id: number | null | undefined) {
  const { data } = useLanguageProfiles();
  return useMemo(() => data?.find((v) => v.profileId === id), [id, data]);
}

export function useEnabledLanguages() {
  const query = useLanguages();

  const enabled = useMemo(() => {
    const data: Language.Info[] =
      query.data
        ?.filter((v) => v.enabled)
        .map<Language.Info>((v) => ({ code2: v.code2, name: v.name })) ?? [];

    return {
      ...query,
      data,
    };
  }, [query]);

  return enabled;
}

// Convert languageprofile items to language
export function useProfileItemsToLanguages(profile?: Language.Profile) {
  const { data } = useLanguages();

  return useMemo(
    () =>
      profile?.items.map<Language.Info>(({ language: code, hi, forced }) => {
        const name = data?.find((v) => v.code2 === code)?.name ?? "";
        return {
          hi: hi === "True",
          forced: forced === "True",
          code2: code,
          name,
        };
      }) ?? [],
    [data, profile?.items],
  );
}

export function useLanguageFromCode3(code3: string) {
  const { data } = useLanguages();

  return useMemo(
    () => data?.find((value) => value.code3 === code3),
    [data, code3],
  );
}

export const normalizeAudioLanguage = (name: string) => {
  return name === "Chinese Simplified" ? "Chinese" : name;
};
