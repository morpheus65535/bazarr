import { useCallback } from "react";
import { useSystemSettings } from "../../apis";
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
  return useReduxStore((s) => s.offline);
}

export function useIsSonarrEnabled() {
  const { data } = useSystemSettings();
  return data?.general.use_sonarr ?? true;
}

export function useIsRadarrEnabled() {
  const { data } = useSystemSettings();
  return data?.general.use_radarr ?? true;
}

export function useShowOnlyDesired() {
  const { data } = useSystemSettings();
  return data?.general.embedded_subs_show_desired ?? false;
}
