import { UPDATE_SERIES_LIST } from "../constants";

import apis from "../../apis";
import { createAsyncAction } from "./creator";

export const updateSeriesList = createAsyncAction(UPDATE_SERIES_LIST, () =>
  apis.series.series()
);
