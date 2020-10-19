import {
  UPDATE_BADGE_EPISODES,
  UPDATE_BADGE_MOVIES,
  UPDATE_BADGE_PROVIDERS,
} from "../constants";

import { createAction } from "redux-actions";
import apis from "../../apis";

export const updateEpisodes = createAction(UPDATE_BADGE_EPISODES, () =>
  apis.badges.series()
);

export const updateMovies = createAction(UPDATE_BADGE_MOVIES, () =>
  apis.badges.movies()
);

export const updateProviders = createAction(UPDATE_BADGE_PROVIDERS, () =>
  apis.badges.providers()
);
