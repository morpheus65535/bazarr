import { CommonState } from "../types";
import {
  AsyncPayload
} from "../types/actions";
import { UPDATE_LANGUAGES_LIST, UPDATE_SERIES_LIST } from "../constants";
import { mapToAsyncState } from "./mapper";

import { handleActions } from "redux-actions";

const reducer = handleActions<CommonState, AsyncPayload<Array<any>>>(
  {
    [UPDATE_LANGUAGES_LIST]: {
      next(state, action) {
        return {
          ...state,
          languages: mapToAsyncState(action, [])
        }
      }
    },
    [UPDATE_SERIES_LIST]: {
      next(state, action) {
        return {
          ...state,
          series: mapToAsyncState(action, [])
        }
      }
    },
  },
  {
    languages: { loading: false, items: [] },
    series: { loading: false, items: [] },
  }
);

export default reducer;
