import { UPDATE_LANGUAGES_LIST, UPDATE_SERIES_LIST } from "../constants";

import apis from "../../apis";
import { createAsyncAction } from "./creator";

export const updateLanguagesList = createAsyncAction(
  UPDATE_LANGUAGES_LIST,
  () => apis.system.languages()
);

export const updateSeriesList = createAsyncAction(UPDATE_SERIES_LIST, () =>
  apis.series.series()
);
