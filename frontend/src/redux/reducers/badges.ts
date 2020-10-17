import { BadgeState } from "../types";
import { UpdateBadgeAction } from "../types/actions";
import {
  UPDATE_BADGE_EPISODES,
  UPDATE_BADGE_MOVIES,
  UPDATE_BADGE_PROVIDERS,
} from "../constants";

export default function badges(
  state: BadgeState,
  action: UpdateBadgeAction
): BadgeState {
  switch (action.type) {
    case UPDATE_BADGE_EPISODES:
      return {
        ...state,
        episodes: action.value,
      };
    case UPDATE_BADGE_MOVIES:
      return {
        ...state,
        movies: action.value,
      };
    case UPDATE_BADGE_PROVIDERS:
      return {
        ...state,
        providers: action.value,
      };
    default:
      return {
        movies: 0,
        episodes: 0,
        providers: 0,
      };
  }
}
