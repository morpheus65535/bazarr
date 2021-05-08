import { useCallback, useEffect } from "react";
import { useSystemSettings } from ".";
import {
  siteAddNotifications,
  siteChangeSidebar,
  siteRemoveNotifications,
} from "../actions";
import { useReduxAction, useReduxStore } from "./base";

export function useNotification(timeout: number = 5000) {
  const add = useReduxAction(siteAddNotifications);
  const remove = useReduxAction(siteRemoveNotifications);

  return useCallback(
    (msg: Omit<ReduxStore.Notification, "timestamp">) => {
      const error: ReduxStore.Notification = {
        ...msg,
        timestamp: new Date(),
      };
      add([error]);
      setTimeout(() => remove([error.timestamp]), timeout);
    },
    [add, remove, timeout]
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
