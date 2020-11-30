import { AsyncAction } from "../types";
import {
  UPDATE_SERIES_EPISODE_LIST,
  UPDATE_SERIES_LIST,
  UPDATE_SERIES_WANTED_LIST,
} from "../constants";
import { mapToAsyncState } from "./mapper";

import { handleActions } from "redux-actions";

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
    [UPDATE_SERIES_EPISODE_LIST]: {
      next(state, action: AsyncAction<Episode[]>) {
        const { updating, lastResult, items } = mapToAsyncState(action, []);

        if (items.length > 0) {
          const id = items[0].sonarrSeriesId;
          const list = state.episodeList.items;
          list.set(id, items);
          return {
            ...state,
            episodeList: {
              updating,
              lastResult,
              items: list,
            },
          };
        } else {
          return {
            ...state,
            episodeList: {
              ...state.episodeList,
              updating,
              lastResult,
            },
          };
        }
      },
    },
  },
  {
    seriesList: { updating: false, items: [] },
    wantedSeriesList: { updating: false, items: [] },
    episodeList: { updating: false, items: new Map() },
  }
);

export default reducer;
