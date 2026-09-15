import { useEffect } from "react";
import { LOG } from "@/utilities/console";
import Socketio from ".";

export const useSocketIOReducer = (reducer: SocketIO.Reducer) => {
  useEffect(() => {
    Socketio.addReducer(reducer);
    LOG("info", "listening to SocketIO event", reducer.key);
    return () => {
      Socketio.removeReducer(reducer);
    };
  }, [reducer]);
};
