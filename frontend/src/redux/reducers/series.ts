import { AsyncPayload } from "../types/actions";
import { UPDATE_SERIES_LIST } from "../constants";
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
  },
  {
    seriesList: { loading: false, items: [] },
  }
);

export default reducer;
