import { AsyncAction } from "../types";
import { UPDATE_SERIES_LIST, UPDATE_SERIES_WANTED_LIST } from "../constants";
import { mapToAsyncState } from "./mapper";

import { handleActions, Action } from "redux-actions";

const reducer = handleActions<SeriesState, any>(
  {
    [UPDATE_SERIES_LIST]: {
      next(state, action: AsyncAction<Series[]>) {
        return {
          ...state,
          seriesList: mapToAsyncState(action, state.seriesList.items),
        };
      },
    },
    [UPDATE_SERIES_WANTED_LIST]: {
      next(state, action: AsyncAction<WantedEpisode[]>) {
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
    seriesList: { updating: false, items: [] },
    wantedSeriesList: { updating: false, items: [] },
  }
);

export default reducer;
