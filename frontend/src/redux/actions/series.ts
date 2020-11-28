import {
  UPDATE_SERIES_LIST,
  UPDATE_SERIES_WANTED_LIST,
  OPEN_SERIES_EDIT_MODAL,
  CLOSE_SERIES_EDIT_MODAL,
} from "../constants";

import apis from "../../apis";
import { createAsyncAction } from "./creator";
import { Action } from "redux-actions";

export const updateSeriesList = createAsyncAction(UPDATE_SERIES_LIST, () =>
  apis.series.series()
);

export const updateWantedSeriesList = createAsyncAction(
  UPDATE_SERIES_WANTED_LIST,
  // TODO: Hardcode to 0 - 25
  () => apis.series.wanted(0, 0, 25)
);

export const openSeriesEditModal = (series: Series): Action<Series> => {
  return {
    type: OPEN_SERIES_EDIT_MODAL,
    payload: series,
  };
};

export const closeSeriesEditModal = (): Action<null> => {
  return {
    type: CLOSE_SERIES_EDIT_MODAL,
    payload: null,
  };
};
