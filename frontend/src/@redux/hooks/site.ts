import { useCallback, useEffect } from "react";
import { useSystemSettings } from ".";
import {
  siteAddNotification,
  siteChangeSidebar,
  siteRemoveNotificationByTime,
} from "../actions";
import { useReduxAction, useReduxStore } from "./base";

export function useNotification(id: string, sec: number = 5) {
  const add = useReduxAction(siteAddNotification);
  const remove = useReduxAction(siteRemoveNotificationByTime);

  return useCallback(
    (msg: Omit<ReduxStore.Notification, "id" | "timestamp">) => {
      const error: ReduxStore.Notification = {
        ...msg,
        id,
        timestamp: new Date(),
      };
      add(error);
      setTimeout(() => remove(error.timestamp), sec * 1000);
    },
    [add, remove, sec, id]
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
