import {
  UPDATE_SERIES_LIST,
  UPDATE_SERIES_WANTED_LIST,
  UPDATE_SERIES_EPISODE_LIST,
  UPDATE_SERIES_HISTORY_LIST,
  UPDATE_SERIES_INFO,
} from "../constants";

import { SeriesApi, EpisodesApi, HistoryApi } from "../../apis";
import { createAsyncAction, createAsyncAction1 } from "./creator";

export const updateSeriesList = createAsyncAction(UPDATE_SERIES_LIST, () =>
  SeriesApi.series()
);

export const updateWantedSeriesList = createAsyncAction(
  UPDATE_SERIES_WANTED_LIST,
  // TODO: Hardcode to 0 - 25
  () => SeriesApi.wanted()
);

export const updateEpisodeList = createAsyncAction1(
  UPDATE_SERIES_EPISODE_LIST,
  (id: number) => EpisodesApi.all(id)
);

export const updateHistorySeriesList = createAsyncAction(
  UPDATE_SERIES_HISTORY_LIST,
  () => HistoryApi.series()
);

export const updateSeriesInfo = createAsyncAction1(
  UPDATE_SERIES_INFO,
  (id: number) => SeriesApi.series(id)
);
