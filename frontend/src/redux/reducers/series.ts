import { AsyncAction } from "../types/actions";
import {
  CLOSE_SERIES_EDIT_MODAL,
  OPEN_SERIES_EDIT_MODAL,
  UPDATE_SERIES_LIST,
  UPDATE_SERIES_WANTED_LIST,
} from "../constants";
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
      next(state, action: AsyncAction<WantedSeries[]>) {
        return {
          ...state,
          wantedSeriesList: mapToAsyncState(
            action,
            state.wantedSeriesList.items
          ),
        };
      },
    },
    [OPEN_SERIES_EDIT_MODAL]: {
      next(state, action: Action<Series>) {
        return {
          ...state,
          seriesModal: action.payload,
        };
      },
    },
    [CLOSE_SERIES_EDIT_MODAL]: {
      next(state, action) {
        return {
          ...state,
          seriesModal: undefined,
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
