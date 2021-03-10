import { Action, handleActions } from "redux-actions";
import { storage } from "../../@storage/local";
import {
  SITE_AUTH_SUCCESS,
  SITE_BADGE_UPDATE,
  SITE_INITIALIZED,
  SITE_NEED_AUTH,
  SITE_NOTIFICATIONS_ADD,
  SITE_NOTIFICATIONS_REMOVE,
  SITE_NOTIFICATIONS_REMOVE_BY_TIMESTAMP,
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
    [SITE_NOTIFICATIONS_ADD]: (
      state,
      action: Action<ReduxStore.Notification>
    ) => {
      const alerts = [
        ...state.notifications.filter((v) => v.id !== action.payload.id),
        action.payload,
      ];
      return { ...state, notifications: alerts };
    },
    [SITE_NOTIFICATIONS_REMOVE]: (state, action: Action<string>) => {
      const alerts = state.notifications.filter((v) => v.id !== action.payload);
      return { ...state, notifications: alerts };
    },
    [SITE_NOTIFICATIONS_REMOVE_BY_TIMESTAMP]: (state, action: Action<Date>) => {
      const alerts = state.notifications.filter(
        (v) => v.timestamp !== action.payload
      );
      return { ...state, notifications: alerts };
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
    notifications: [],
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
