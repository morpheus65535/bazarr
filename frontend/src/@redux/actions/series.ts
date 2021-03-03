import { EpisodesApi, SeriesApi } from "../../apis";
import {
  SERIES_UPDATE_BLACKLIST,
  SERIES_UPDATE_EPISODE_LIST,
  SERIES_UPDATE_HISTORY_LIST,
  SERIES_UPDATE_INFO,
  SERIES_UPDATE_WANTED_LIST,
} from "../constants";
import { badgeUpdateSeries } from "./badges";
import { createAsyncAction, createCombineAction } from "./utils";

const seriesUpdateWantedList = createAsyncAction(
  SERIES_UPDATE_WANTED_LIST,
  () => EpisodesApi.wanted()
);

export const seriesUpdateWantedAll = createCombineAction(() => [
  seriesUpdateWantedList(),
  badgeUpdateSeries(),
]);

export const episodeUpdateBySeriesId = createAsyncAction(
  SERIES_UPDATE_EPISODE_LIST,
  (seriesid: number) => EpisodesApi.bySeriesId(seriesid)
);

export const seriesUpdateHistoryList = createAsyncAction(
  SERIES_UPDATE_HISTORY_LIST,
  () => EpisodesApi.history()
);

const seriesUpdateInfo = createAsyncAction(SERIES_UPDATE_INFO, (id?: number) =>
  SeriesApi.series(id)
);

export const seriesUpdateInfoAll = createCombineAction((id?: number) => {
  const actions: any[] = [seriesUpdateInfo(id), badgeUpdateSeries()];
  if (id !== undefined) {
    actions.push(episodeUpdateBySeriesId(id));
  }
  return actions;
});

export const seriesUpdateBlacklist = createAsyncAction(
  SERIES_UPDATE_BLACKLIST,
  () => EpisodesApi.blacklist()
);
