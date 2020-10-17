import { UpdateEpisodesAction, UpdateMoviesAction, UpdateProvidersAction } from "../types/actions"
import { UPDATE_BADGE_EPISODES, UPDATE_BADGE_MOVIES, UPDATE_BADGE_PROVIDERS } from "../constants";

export function updateEpisodes(val: number): UpdateEpisodesAction {
  return {
    type: UPDATE_BADGE_EPISODES,
    value: val
  }
}

export function updateMovies(val: number): UpdateMoviesAction {
  return {
    type: UPDATE_BADGE_MOVIES,
    value: val,
  };
}

export function updateProviders(val: number): UpdateProvidersAction {
  return {
    type: UPDATE_BADGE_PROVIDERS,
    value: val,
  };
}