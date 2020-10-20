import {} from "redux-thunk";
import { Dispatch } from "redux";
import { AsyncAction } from "../types/actions";

function asyncTrunkCreator<P, R>(
  type: string,
  promise: (args?: R) => Promise<P>
) {
  return (dispatch: Dispatch<AsyncAction<P>>) => {
    dispatch({
      type,
      payload: {
        loading: true,
      },
    });
    promise()
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
  return () => asyncTrunkCreator(type, promise);
}
