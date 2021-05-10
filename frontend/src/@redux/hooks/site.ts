import { useCallback, useEffect } from "react";
import { useSystemSettings } from ".";
import { siteAddNotifications, siteChangeSidebar } from "../actions";
import { useReduxAction, useReduxStore } from "./base";

export function useNotification(id: string, timeout: number = 5000) {
  const add = useReduxAction(siteAddNotifications);

  return useCallback(
    (msg: Omit<ReduxStore.Notification, "id" | "timeout">) => {
      const notification: ReduxStore.Notification = {
        ...msg,
        id,
        timeout,
      };
      add([notification]);
    },
    [add, timeout, id]
  );
}

export function useIsOffline() {
  return useReduxStore((s) => s.site.offline);
}

export function useIsSonarrEnabled() {
  const [settings] = useSystemSettings();
  return settings.data?.general.use_sonarr ?? true;
}

export function useIsRadarrEnabled() {
  const [settings] = useSystemSettings();
  return settings.data?.general.use_radarr ?? true;
}

export function useShowOnlyDesired() {
  const [settings] = useSystemSettings();
  return settings.data?.general.embedded_subs_show_desired ?? false;
}

export function useSetSidebar(key: string) {
  const update = useReduxAction(siteChangeSidebar);
  useEffect(() => {
    update(key);
  }, [update, key]);
}
