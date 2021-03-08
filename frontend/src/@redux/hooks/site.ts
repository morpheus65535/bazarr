import { useCallback } from "react";
import { siteAddError, siteRemoveErrorWithTimestamp } from "../actions";
import { useReduxAction } from "./base";

export function useDispatchError(id: string, sec: number = 5) {
  const add = useReduxAction(siteAddError);
  const remove = useReduxAction(siteRemoveErrorWithTimestamp);

  return useCallback(
    (err: Omit<ReduxStore.Error, "id" | "timestamp">) => {
      const error: ReduxStore.Error = {
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
