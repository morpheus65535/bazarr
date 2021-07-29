import { ActionCreator } from "@reduxjs/toolkit";
import { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from "../store";

// function use
export function useReduxStore<T extends (store: RootState) => any>(
  selector: T
) {
  return useSelector<RootState, ReturnType<T>>(selector);
}

export function useReduxAction<T extends ActionCreator<any>>(action: T) {
  const dispatch = useDispatch<AppDispatch>();
  return useCallback((...args: Parameters<T>) => dispatch(action(...args)), [
    action,
    dispatch,
  ]);
}
