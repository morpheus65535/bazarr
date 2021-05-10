import { useCallback, useEffect } from "react";
import Socketio from ".";
import { log } from "../utilites/logger";

export function useSocketIOReducer(reducer: SocketIO.Reducer) {
  useEffect(() => {
    Socketio.addReducer(reducer);
    log("info", "listening to SocketIO event", reducer.key);
    return () => {
      Socketio.removeReducer(reducer);
    };
  }, [reducer]);
}

export function useWrapToOptionalId(
  fn: (id: number[]) => void
): SocketIO.ActionFn<number> {
  return useCallback(
    (id?: number[]) => {
      if (id) {
        fn(id);
      }
    },
    [fn]
  );
}
