import { isEqual } from "lodash";
import { log } from "../../utilites/logger";
import {
  ActionCallback,
  ActionDispatcher,
  AsyncActionCreator,
  AsyncActionDispatcher,
  AvailableCreator,
  AvailableType,
  PromiseCreator,
} from "../types";

// Limiter the call to API
const gLimiter: Map<PromiseCreator, Date> = new Map();
const gArgs: Map<PromiseCreator, any[]> = new Map();

const LIMIT_CALL_MS = 200;

function asyncActionFactory<T extends PromiseCreator>(
  type: string,
  promise: T,
  args: Parameters<T>
): AsyncActionDispatcher<PromiseType<ReturnType<T>>> {
  return (dispatch) => {
    const previousArgs = gArgs.get(promise);
    const date = new Date();

    if (isEqual(previousArgs, args)) {
      // Get last execute date
      const previousExec = gLimiter.get(promise);
      if (previousExec) {
        const distInMs = date.getTime() - previousExec.getTime();
        if (distInMs < LIMIT_CALL_MS) {
          log(
            "warning",
            "Multiple calls to API within the range",
            promise,
            args
          );
          return Promise.resolve();
        }
      }
    } else {
      gArgs.set(promise, args);
    }

    gLimiter.set(promise, date);

    dispatch({
      type,
      payload: {
        loading: true,
        parameters: args,
      },
    });

    return new Promise((resolve, reject) => {
      promise(...args)
        .then((val) => {
          dispatch({
            type,
            payload: {
              loading: false,
              item: val,
              parameters: args,
            },
          });
          resolve();
        })
        .catch((err) => {
          dispatch({
            type,
            error: true,
            payload: {
              loading: false,
              item: err,
              parameters: args,
            },
          });
          reject(err);
        });
    });
  };
}

export function createAsyncAction<T extends PromiseCreator>(
  type: string,
  promise: T
) {
  return (...args: Parameters<T>) => asyncActionFactory(type, promise, args);
}

// Create a action which combine multiple ActionDispatcher and execute them at once
function combineActionFactory(
  dispatchers: AvailableType<any>[]
): ActionDispatcher {
  return (dispatch) => {
    dispatchers.forEach((fn) => {
      if (typeof fn === "function") {
        fn(dispatch);
      } else {
        dispatch(fn);
      }
    });
  };
}

export function createCombineAction<T extends AvailableCreator>(fn: T) {
  return (...args: Parameters<T>) => combineActionFactory(fn(...args));
}

function combineAsyncActionFactory(
  dispatchers: AsyncActionDispatcher<any>[]
): AsyncActionDispatcher<any> {
  return (dispatch) => {
    const promises = dispatchers.map((v) => v(dispatch));
    return Promise.all(promises) as Promise<any>;
  };
}

export function createAsyncCombineAction<T extends AsyncActionCreator>(fn: T) {
  return (...args: Parameters<T>) => combineAsyncActionFactory(fn(...args));
}

export function callbackActionFactory(
  dispatchers: AsyncActionDispatcher<any>[],
  success: ActionCallback,
  error?: ActionCallback
): ActionDispatcher<any> {
  return (dispatch) => {
    const promises = dispatchers.map((v) => v(dispatch));
    Promise.all(promises)
      .then(() => {
        const action = success();
        if (action !== undefined) {
          dispatch(action);
        }
      })
      .catch(() => {
        const action = error && error();
        if (action !== undefined) {
          dispatch(action);
        }
      });
  };
}

export function createCallbackAction<T extends AsyncActionCreator>(
  fn: T,
  success: ActionCallback,
  error?: ActionCallback
) {
  return (...args: Parameters<T>) =>
    callbackActionFactory(fn(args), success, error);
}
