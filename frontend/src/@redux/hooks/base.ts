import { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "../store";

// function use
export function useReduxStore<T extends (store: RootState) => any>(
  selector: T
) {
  return useSelector<RootState, ReturnType<T>>(selector);
}

export function useReduxAction<T extends (...args: any[]) => void>(action: T) {
  const dispatch = useDispatch();
  return useCallback((...args: Parameters<T>) => dispatch(action(...args)), [
    action,
    dispatch,
  ]);
}
