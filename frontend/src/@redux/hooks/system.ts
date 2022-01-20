import { useMemo } from "react";
import { useLanguageProfiles, useLanguages } from "../../apis";
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

export function useProfileBy(id: number | null | undefined) {
  const { data } = useLanguageProfiles();
  return useMemo(() => data?.find((v) => v.profileId === id), [id, data]);
}

export function useEnabledLanguages() {
  const query = useLanguages();

  const enabled = useMemo(() => {
    const data =
      query.data
        ?.filter((v) => v.enabled)
        .map((v) => ({ code2: v.code2, name: v.name })) ?? [];

    return {
      ...query,
      data,
    };
  }, [query]);

  return enabled;
}

export function useLanguageBy(code?: string) {
  const { data } = useLanguages();
  return useMemo(() => data?.find((v) => v.code2 === code), [data, code]);
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
    [data, profile?.items]
  );
}
