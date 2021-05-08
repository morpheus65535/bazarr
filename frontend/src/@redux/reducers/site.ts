import { Action, handleActions } from "redux-actions";
import apis from "../../apis";
import {
  SITE_BADGE_UPDATE,
  SITE_INITIALIZED,
  SITE_INITIALIZE_FAILED,
  SITE_NEED_AUTH,
  SITE_NOTIFICATIONS_ADD,
  SITE_NOTIFICATIONS_REMOVE,
  SITE_NOTIFICATIONS_REMOVE_BY_TIMESTAMP,
  SITE_OFFLINE_UPDATE,
  SITE_SIDEBAR_UPDATE,
} from "../constants";
import { AsyncAction } from "../types";

const reducer = handleActions<ReduxStore.Site, any>(
  {
    [SITE_NEED_AUTH]: (state) => {
      if (process.env.NODE_ENV !== "development") {
        apis.danger_resetApi("NEED_AUTH");
      }
      return {
        ...state,
        auth: false,
      };
    },
    [SITE_INITIALIZED]: (state) => ({
      ...state,
      initialized: true,
    }),
    [SITE_INITIALIZE_FAILED]: (state) => ({
      ...state,
      initialized: "An Error Occurred When Initializing Bazarr UI",
    }),
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
      next: (state, action: AsyncAction<Badge>) => {
        const badges = action.payload.item;
        if (badges && action.error !== true) {
          return { ...state, badges: badges as Badge };
        }
        return state;
      },
      throw: (state) => state,
    },
    [SITE_OFFLINE_UPDATE]: (state, action: Action<boolean>) => {
      return { ...state, offline: action.payload };
    },
  },
  {
    initialized: false,
    auth: true,
    notifications: [],
    sidebar: "",
    badges: {
      movies: 0,
      episodes: 0,
      providers: 0,
      status: 0,
    },
    offline: false,
  }
);

export default reducer;
