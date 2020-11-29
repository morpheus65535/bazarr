import { UPDATE_SERIES_LIST, UPDATE_SERIES_WANTED_LIST } from "../constants";

import apis from "../../apis";
import { createAsyncAction } from "./creator";

export const updateSeriesList = createAsyncAction(UPDATE_SERIES_LIST, () =>
  apis.series.series()
);

export const updateWantedSeriesList = createAsyncAction(
  UPDATE_SERIES_WANTED_LIST,
  // TODO: Hardcode to 0 - 25
  () => apis.series.wanted(0, 0, 25)
);
