import {
  UPDATE_SERIES_LIST,
  UPDATE_SERIES_WANTED_LIST,
  UPDATE_SERIES_EPISODE_LIST,
  UPDATE_SERIES_HISTORY_LIST,
  UPDATE_SERIES_INFO,
} from "../constants";

import { SeriesApi, EpisodesApi, HistoryApi } from "../../apis";
import { createAsyncAction, createCombineAction } from "./utils";

import { updateBadges } from "./badges";

export const updateSeriesList = createAsyncAction(UPDATE_SERIES_LIST, () =>
  SeriesApi.series()
);

export const updateWantedSeriesList = createAsyncAction(
  UPDATE_SERIES_WANTED_LIST,
  () => SeriesApi.wanted()
);

export const updateEpisodeList = createAsyncAction(
  UPDATE_SERIES_EPISODE_LIST,
  (id: number) => EpisodesApi.all(id)
);

export const updateHistorySeriesList = createAsyncAction(
  UPDATE_SERIES_HISTORY_LIST,
  () => HistoryApi.series()
);

export const updateSeries = createAsyncAction(
  UPDATE_SERIES_INFO,
  (id: number) => SeriesApi.series(id)
);

export const updateSeriesInfo = createCombineAction((id: number) => [
  updateSeries(id),
  updateEpisodeList(id),
  updateBadges(),
]);
