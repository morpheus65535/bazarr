import { useSystemSettings } from "@/apis/hooks";
import { useCallback } from "react";
import { addNotifications } from "../actions";
import { useReduxAction, useReduxStore } from "./base";

export function useNotification(id: string, timeout = 5000) {
  const add = useReduxAction(addNotifications);

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

export function useEnabledStatus() {
  const { data } = useSystemSettings();

  return {
    sonarr: data?.general.use_sonarr ?? false,
    radarr: data?.general.use_radarr ?? false,
  };
}

export function useShowOnlyDesired() {
  const { data } = useSystemSettings();
  return data?.general.embedded_subs_show_desired ?? false;
}
