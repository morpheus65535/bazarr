import {
  UPDATE_SERIES_LIST,
  UPDATE_SERIES_WANTED_LIST,
  UPDATE_SERIES_EPISODE_LIST,
  UPDATE_SERIES_HISTORY_LIST,
} from "../constants";

import apis from "../../apis";
import { createAsyncAction, createAsyncAction1 } from "./creator";

export const updateSeriesList = createAsyncAction(UPDATE_SERIES_LIST, () =>
  apis.series.series()
);

export const updateWantedSeriesList = createAsyncAction(
  UPDATE_SERIES_WANTED_LIST,
  // TODO: Hardcode to 0 - 25
  () => apis.series.wanted(0, 0, 25)
);

export const updateEpisodeList = createAsyncAction1(
  UPDATE_SERIES_EPISODE_LIST,
  (id: number) => apis.series.episodes(id)
);

export const updateHistorySeriesList = createAsyncAction(
  UPDATE_SERIES_HISTORY_LIST,
  () => apis.series.history()
);
