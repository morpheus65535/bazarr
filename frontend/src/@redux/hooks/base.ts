import { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";

// function use
export function useReduxStore<T extends (store: ReduxStore) => any>(
  selector: T
) {
  return useSelector<ReduxStore, ReturnType<T>>(selector);
}

export function useReduxAction<T extends (...args: any[]) => any>(action: T) {
  const dispatch = useDispatch();
  return useCallback(
    (...args: Parameters<T>) => {
      dispatch(action(...args));
    },
    [action, dispatch]
  );
}
