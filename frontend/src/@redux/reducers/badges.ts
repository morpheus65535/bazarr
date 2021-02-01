import { handleActions } from "redux-actions";
import {
  BADGE_UPDATE_MOVIES,
  BADGE_UPDATE_PROVIDERS,
  BADGE_UPDATE_SERIES,
} from "../constants";

const reducer = handleActions<BadgeState, number>(
  {
    [BADGE_UPDATE_MOVIES]: {
      next(state, action) {
        return {
          ...state,
          movies: action.payload,
        };
      },
    },
    [BADGE_UPDATE_SERIES]: {
      next(state, action) {
        return {
          ...state,
          episodes: action.payload,
        };
      },
    },
    [BADGE_UPDATE_PROVIDERS]: {
      next(state, action) {
        return {
          ...state,
          providers: action.payload,
        };
      },
    },
  },
  {
    movies: 0,
    episodes: 0,
    providers: 0,
  }
);

export default reducer;
