import { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { AnyActionCreator } from "../actions/types";
import { AppDispatch, RootState } from "../store";

export function useReduxStore<R, S = RootState>(selector: (store: S) => R) {
  return useSelector<S, R>(selector);
}

export function useAppDispatch() {
  return useDispatch<AppDispatch>();
}

export function useReduxAction<A extends AnyActionCreator>(action: A) {
  const dispatch = useAppDispatch();
  return useCallback(
    (...args: Parameters<A>) => dispatch(action(...args)),
    [action, dispatch]
  );
}
