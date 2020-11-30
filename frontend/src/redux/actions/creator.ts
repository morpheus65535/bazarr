import {} from "redux-thunk";
import { Dispatch } from "redux";
import { AsyncAction } from "../types";

function asyncActionCreator<P>(
  type: string,
  promise: (...args: any[]) => Promise<P>,
  ...args: any[]
) {
  return (dispatch: Dispatch<AsyncAction<P>>) => {
    dispatch({
      type,
      payload: {
        loading: true,
      },
    });
    promise(...args)
      .then((val) => {
        dispatch({
          type,
          payload: {
            loading: false,
            item: val,
          },
        });
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
      });
  };
}

export function createAsyncAction<P>(type: string, promise: () => Promise<P>) {
  return () => asyncActionCreator(type, promise);
}

export function createAsyncAction1<P, ARG1>(
  type: string,
  promise: (arg: ARG1) => Promise<P>
) {
  return (arg: ARG1) => asyncActionCreator(type, promise, arg);
}
