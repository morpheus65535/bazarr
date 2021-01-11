import { UPDATE_BADGE_ALL } from "../constants";

import { createAction } from "redux-actions";
import { BadgesApi } from "../../apis";

export const updateBadges = createAction(UPDATE_BADGE_ALL, () =>
  Promise.all([BadgesApi.series(), BadgesApi.movies(), BadgesApi.providers()])
);
