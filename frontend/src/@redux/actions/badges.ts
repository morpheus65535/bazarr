import {
  UPDATE_BADGE_EPISODES,
  UPDATE_BADGE_MOVIES,
  UPDATE_BADGE_PROVIDERS,
} from "../constants";

import { createAction } from "redux-actions";
import { BadgesApi } from "../../apis";

export const updateEpisodes = createAction(UPDATE_BADGE_EPISODES, () =>
  BadgesApi.series()
);

export const updateMovies = createAction(UPDATE_BADGE_MOVIES, () =>
  BadgesApi.movies()
);

export const updateProviders = createAction(UPDATE_BADGE_PROVIDERS, () =>
  BadgesApi.providers()
);
