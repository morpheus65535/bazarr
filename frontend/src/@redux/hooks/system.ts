import { useMemo } from "react";
import { useSocketIOReducer } from "../../@socketio/hooks";
import {
  providerUpdateList,
  systemUpdateAllSettings,
  systemUpdateHealth,
  systemUpdateLanguages,
  systemUpdateLanguagesProfiles,
  systemUpdateLogs,
  systemUpdateReleases,
  systemUpdateStatus,
  systemUpdateTasks,
} from "../actions";
import { useAutoUpdateItem } from "./async";
import { stateBuilder, useReduxAction, useReduxStore } from "./base";

export function useSystemSettings() {
  const update = useReduxAction(systemUpdateAllSettings);
  const items = useReduxStore((s) => s.system.settings);

  return stateBuilder(items, update);
}

export function useSystemLogs() {
  const items = useReduxStore(({ system }) => system.logs);
  const update = useReduxAction(systemUpdateLogs);

  useAutoUpdateItem(items, update);
  return stateBuilder(items, update);
}

export function useSystemTasks() {
  const items = useReduxStore((s) => s.system.tasks);
  const update = useReduxAction(systemUpdateTasks);
  const reducer = useMemo<SocketIO.Reducer>(
    () => ({ key: "task", update }),
    [update]
  );
  useSocketIOReducer(reducer);

  useAutoUpdateItem(items, update);
  return stateBuilder(items, update);
}

export function useSystemStatus() {
  const items = useReduxStore((s) => s.system.status);
  const update = useReduxAction(systemUpdateStatus);

  useAutoUpdateItem(items, update);
  return stateBuilder(items.content, update);
}

export function useSystemHealth() {
  const items = useReduxStore((s) => s.system.health);
  const update = useReduxAction(systemUpdateHealth);

  useAutoUpdateItem(items, update);
  return stateBuilder(items, update);
}

export function useSystemProviders() {
  const update = useReduxAction(providerUpdateList);
  const items = useReduxStore((d) => d.system.providers);

  useAutoUpdateItem(items, update);
  return stateBuilder(items, update);
}

export function useSystemReleases() {
  const items = useReduxStore(({ system }) => system.releases);
  const update = useReduxAction(systemUpdateReleases);

  useAutoUpdateItem(items, update);
  return stateBuilder(items, update);
}

export function useLanguageProfiles() {
  const action = useReduxAction(systemUpdateLanguagesProfiles);
  const { content } = useReduxStore((s) => s.system.languagesProfiles);

  return stateBuilder(content, action);
}

export function useProfileBy(id: number | null | undefined) {
  const [profiles] = useLanguageProfiles();
  return useMemo(
    () => profiles.find((v) => v.profileId === id),
    [id, profiles]
  );
}

export function useLanguages() {
  const action = useReduxAction(systemUpdateLanguages);
  const data = useReduxStore((s) => s.system.languages);

  const languages = useMemo<Language.Info[]>(
    () => data.content.map((v) => ({ code2: v.code2, name: v.name })),
    [data.content]
  );

  return stateBuilder(languages, action);
}

export function useEnabledLanguages() {
  const action = useReduxAction(systemUpdateLanguages);
  const data = useReduxStore((s) => s.system.languages);

  const enabled = useMemo<Language.Info[]>(
    () =>
      data.content
        .filter((v) => v.enabled)
        .map((v) => ({ code2: v.code2, name: v.name })),
    [data.content]
  );

  return stateBuilder(enabled, action);
}

export function useLanguageBy(code?: string) {
  const [languages] = useLanguages();
  return useMemo(
    () => languages.find((v) => v.code2 === code),
    [languages, code]
  );
}

// Convert languageprofile items to language
export function useProfileItems(profile?: Language.Profile) {
  const [languages] = useLanguages();

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
