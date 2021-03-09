import { Action, handleActions } from "redux-actions";
import { storage } from "../../@storage/local";
import {
  SITE_AUTH_SUCCESS,
  SITE_BADGE_UPDATE,
  SITE_ERROR_ADD,
  SITE_ERROR_REMOVE,
  SITE_ERROR_REMOVE_WITH_TIMESTAMP,
  SITE_INITIALIZED,
  SITE_NEED_AUTH,
  SITE_SAVE_LOCALSTORAGE,
  SITE_SIDEBAR_UPDATE,
} from "../constants";

function updateLocalStorage(): Partial<ReduxStore.Site> {
  return {
    pageSize: storage.pageSize,
  };
}

const reducer = handleActions<ReduxStore.Site, any>(
  {
    [SITE_NEED_AUTH]: (state) => ({
      ...state,
      auth: false,
    }),
    [SITE_AUTH_SUCCESS]: (state) => ({
      ...state,
      auth: true,
    }),
    [SITE_INITIALIZED]: (state) => ({
      ...state,
      initialized: true,
    }),
    [SITE_SAVE_LOCALSTORAGE]: (state, action: Action<LooseObject>) => {
      const settings = action.payload;
      for (const key in settings) {
        const value = settings[key];
        localStorage.setItem(key, value);
      }
      return {
        ...state,
        ...updateLocalStorage(),
      };
    },
    [SITE_ERROR_ADD]: (state, action: Action<ReduxStore.Error>) => {
      const alerts = [
        ...state.alerts.filter((v) => v.id !== action.payload.id),
        action.payload,
      ];
      return { ...state, alerts };
    },
    [SITE_ERROR_REMOVE]: (state, action: Action<string>) => {
      const alerts = state.alerts.filter((v) => v.id !== action.payload);
      return { ...state, alerts };
    },
    [SITE_ERROR_REMOVE_WITH_TIMESTAMP]: (state, action: Action<Date>) => {
      const alerts = state.alerts.filter((v) => v.timestamp !== action.payload);
      return { ...state, alerts };
    },
    [SITE_SIDEBAR_UPDATE]: (state, action: Action<string>) => {
      return {
        ...state,
        sidebar: action.payload,
      };
    },
    [SITE_BADGE_UPDATE]: {
      next: (state, action: Action<Badge>) => {
        return { ...state, badges: action.payload };
      },
      throw: (state) => state,
    },
  },
  {
    initialized: false,
    auth: true,
    pageSize: 50,
    alerts: [],
    sidebar: "",
    badges: {
      movies: 0,
      episodes: 0,
      providers: 0,
    },
    ...updateLocalStorage(),
  }
);

export default reducer;
