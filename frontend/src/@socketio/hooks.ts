import { useEffect, useMemo } from "react";
import Socketio from ".";

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
    return () => {
      Socketio.removeReducer(reducer);
    };
  }, [reducer]);
}
