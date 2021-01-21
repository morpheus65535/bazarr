import {
  UPDATE_BADGE_MOVIES,
  UPDATE_BADGE_PROVIDERS,
  UPDATE_BADGE_SERIES,
} from "../constants";

import { createAction } from "redux-actions";
import { createCombineAction } from "./utils";
import { BadgesApi } from "../../apis";

export const updateBadges = createCombineAction(() => [
  updateBadgeMovies(),
  updateBadgeSeries(),
  updateBadgeProviders(),
]);

export const updateBadgeMovies = createAction(UPDATE_BADGE_MOVIES, () =>
  BadgesApi.movies()
);

export const updateBadgeSeries = createAction(UPDATE_BADGE_SERIES, () =>
  BadgesApi.series()
);

export const updateBadgeProviders = createAction(UPDATE_BADGE_PROVIDERS, () =>
  BadgesApi.providers()
);
