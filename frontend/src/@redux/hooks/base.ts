import { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { createCallbackAction } from "../actions/factory";
import { ActionSuccessCallback, AsyncActionDispatcher } from "../types";

// function use
export function useReduxStore<T extends (store: ReduxStore) => any>(
  selector: T
) {
  return useSelector<ReduxStore, ReturnType<T>>(selector);
}

export function useReduxAction<T extends (...args: any[]) => any>(action: T) {
  const dispatch = useDispatch();
  return useCallback((...args: Parameters<T>) => dispatch(action(...args)), [
    action,
    dispatch,
  ]);
}

export function useReduxActionWith<
  T extends (...args: any[]) => AsyncActionDispatcher<any>
>(action: T, success: ActionSuccessCallback) {
  const dispatch = useDispatch();
  return useCallback(
    (...args: Parameters<T>) => {
      const callbackAction = createCallbackAction(
        () => [action(...args)],
        success
      );

      dispatch(callbackAction());
    },
    [dispatch, action, success]
  );
}
