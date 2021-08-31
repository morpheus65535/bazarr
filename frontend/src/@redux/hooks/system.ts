import { useMemo } from "react";
import {
  providerUpdateList,
  systemUpdateHealth,
  systemUpdateLogs,
  systemUpdateReleases,
  systemUpdateStatus,
  systemUpdateTasks,
} from "../actions";
import { useAutoUpdate } from "./async";
import { useReduxAction, useReduxStore } from "./base";

export function useSystemSettings() {
  const items = useReduxStore((s) => s.system.settings);

  return items;
}

export function useSystemLogs() {
  const items = useReduxStore(({ system }) => system.logs);
  const update = useReduxAction(systemUpdateLogs);

  useAutoUpdate(items, update);
  return items;
}

export function useSystemTasks() {
  const items = useReduxStore((s) => s.system.tasks);
  const update = useReduxAction(systemUpdateTasks);

  useAutoUpdate(items, update);
  return items;
}

export function useSystemStatus() {
  const items = useReduxStore((s) => s.system.status);
  const update = useReduxAction(systemUpdateStatus);

  useAutoUpdate(items, update);
  return items.content;
}

export function useSystemHealth() {
  const items = useReduxStore((s) => s.system.health);
  const update = useReduxAction(systemUpdateHealth);

  useAutoUpdate(items, update);
  return items;
}

export function useSystemProviders() {
  const update = useReduxAction(providerUpdateList);
  const items = useReduxStore((d) => d.system.providers);

  useAutoUpdate(items, update);
  return items;
}

export function useSystemReleases() {
  const items = useReduxStore(({ system }) => system.releases);
  const update = useReduxAction(systemUpdateReleases);

  useAutoUpdate(items, update);
  return items;
}

export function useLanguageProfiles() {
  const items = useReduxStore((s) => s.system.languagesProfiles);

  return items.content;
}

export function useProfileBy(id: number | null | undefined) {
  const profiles = useLanguageProfiles();
  return useMemo(
    () => profiles?.find((v) => v.profileId === id),
    [id, profiles]
  );
}

export function useLanguages() {
  const data = useReduxStore((s) => s.system.languages);

  const languages = useMemo<Language.Info[]>(
    () => data.content?.map((v) => ({ code2: v.code2, name: v.name })) ?? [],
    [data.content]
  );

  return languages;
}

export function useEnabledLanguages() {
  const data = useReduxStore((s) => s.system.languages);

  const enabled = useMemo<Language.Info[]>(
    () =>
      data.content
        ?.filter((v) => v.enabled)
        .map((v) => ({ code2: v.code2, name: v.name })) ?? [],
    [data.content]
  );

  return enabled;
}

export function useLanguageBy(code?: string) {
  const languages = useLanguages();
  return useMemo(
    () => languages.find((v) => v.code2 === code),
    [languages, code]
  );
}

// Convert languageprofile items to language
export function useProfileItemsToLanguages(profile?: Language.Profile) {
  const languages = useLanguages();

  return useMemo(
    () =>
      profile?.items.map<Language.Info>(({ language: code, hi, forced }) => {
        const name = languages.find((v) => v.code2 === code)?.name ?? "";
        return {
          hi: hi === "True",
          forced: forced === "True",
          code2: code,
          name,
        };
      }) ?? [],
    [languages, profile?.items]
  );
}
