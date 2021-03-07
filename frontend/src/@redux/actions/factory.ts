import {
  ActionDispatcher,
  ActionSuccessCallback,
  AsyncActionCreator,
  AsyncActionDispatcher,
  AvaliableCreator,
  AvaliableType,
  PromiseCreator,
} from "../types";

function asyncActionFactory<T extends PromiseCreator>(
  type: string,
  promise: T,
  args: Parameters<T>
): AsyncActionDispatcher<PromiseType<ReturnType<T>>> {
  return (dispatch) => {
    dispatch({
      type,
      payload: {
        loading: true,
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
  dispatchers: AvaliableType<any>[]
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

export function createCombineAction<T extends AvaliableCreator>(fn: T) {
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
  success: ActionSuccessCallback
): ActionDispatcher<any> {
  return (dispatch) => {
    const promises = dispatchers.map((v) => v(dispatch));
    Promise.all(promises).then(() => {
      const action = success();
      if (action !== undefined) {
        dispatch(action);
      }
    });
  };
}

export function createCallbackAction<T extends AsyncActionCreator>(
  fn: T,
  success: ActionSuccessCallback
) {
  return (...args: Parameters<T>) => callbackActionFactory(fn(args), success);
}
