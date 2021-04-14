import { useCallback, useEffect, useMemo } from "react";
import Socketio from ".";
import { log } from "../utilites/logger";

export function useSocketIOReducer(
  key: SocketIO.EventType,
  any?: () => void,
  update?: SocketIO.ActionFn,
  remove?: SocketIO.ActionFn
) {
  const reducer = useMemo<SocketIO.Reducer>(
    () => ({ key, any, update, delete: remove }),
    [key, any, update, remove]
  );
  useEffect(() => {
    Socketio.addReducer(reducer);
    log("info", "listening to SocketIO event", key);
    return () => {
      Socketio.removeReducer(reducer);
    };
  }, [reducer, key]);
}

export function useWrapToOptionalId(
  fn: (id: number[]) => void
): SocketIO.ActionFn {
  return useCallback(
    (id?: number[]) => {
      if (id) {
        fn(id);
      }
    },
    [fn]
  );
}
