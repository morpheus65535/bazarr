import { useCallback } from "react";
import { siteAddError, siteRemoveErrorByTimestamp } from "../actions";
import { useReduxAction, useReduxStore } from "./base";

export function useNotification(id: string, sec: number = 5) {
  const add = useReduxAction(siteAddError);
  const remove = useReduxAction(siteRemoveErrorByTimestamp);

  return useCallback(
    (err: Omit<ReduxStore.Notification, "id" | "timestamp">) => {
      const error: ReduxStore.Notification = {
        ...err,
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
