import { createAction } from "redux-actions";
import { BadgesApi } from "../../apis";
import {
  BADGE_UPDATE_MOVIES,
  BADGE_UPDATE_PROVIDERS,
  BADGE_UPDATE_SERIES,
} from "../constants";
import { createCombineAction } from "./utils";

export const updateBadges = createCombineAction(() => [
  badgeUpdateMovies(),
  badgeUpdateSeries(),
  badgeUpdateProviders(),
]);

export const badgeUpdateMovies = createAction(BADGE_UPDATE_MOVIES, () =>
  BadgesApi.movies()
);

export const badgeUpdateSeries = createAction(BADGE_UPDATE_SERIES, () =>
  BadgesApi.series()
);

export const badgeUpdateProviders = createAction(BADGE_UPDATE_PROVIDERS, () =>
  BadgesApi.providers()
);
