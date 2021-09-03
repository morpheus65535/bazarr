import { useCallback } from "react";
import { useSystemSettings } from ".";
import { siteAddNotifications } from "../actions";
import { useReduxAction, useReduxStore } from "./base";

export function useNotification(id: string, timeout: number = 5000) {
  const add = useReduxAction(siteAddNotifications);

  return useCallback(
    (msg: Omit<Server.Notification, "id" | "timeout">) => {
      const notification: Server.Notification = {
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

export function useIsSeriesEnabled() {
  const settings = useSystemSettings();
  return settings.content?.general.use_series ?? true;
}

export function useIsMoviesEnabled() {
  const settings = useSystemSettings();
  return settings.content?.general.use_movies ?? true;
}

export function useShowOnlyDesired() {
  const settings = useSystemSettings();
  return settings.content?.general.embedded_subs_show_desired ?? false;
}
