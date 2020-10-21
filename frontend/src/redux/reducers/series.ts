import { AsyncPayload } from "../types/actions";
import { UPDATE_SERIES_LIST, UPDATE_SERIES_WANTED_LIST } from "../constants";
import { mapToAsyncState } from "./mapper";

import { handleActions } from "redux-actions";

const reducer = handleActions<SeriesState, AsyncPayload<Array<any>>>(
  {
    [UPDATE_SERIES_LIST]: {
      next(state, action) {
        return {
          ...state,
          seriesList: mapToAsyncState(action, state.seriesList.items),
        };
      },
    },
    [UPDATE_SERIES_WANTED_LIST]: {
      next(state, action) {
        return {
          ...state,
          wantedSeriesList: mapToAsyncState(
            action,
            state.wantedSeriesList.items
          ),
        };
      },
    },
  },
  {
    seriesList: { loading: false, items: [] },
    wantedSeriesList: { loading: false, items: [] },
  }
);

export default reducer;
