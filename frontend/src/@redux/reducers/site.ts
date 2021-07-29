import { createReducer } from "@reduxjs/toolkit";
import { remove, uniqBy } from "lodash";
import apis from "../../apis";
import {
  siteAddNotifications,
  siteAddProgress,
  siteBootstrap,
  siteChangeSidebar,
  siteRedirectToAuth,
  siteRemoveNotifications,
  siteRemoveProgress,
  siteUpdateBadges,
  siteUpdateInitialization,
  siteUpdateOffline,
} from "../actions/site";

interface Site {
  // Initialization state or error message
  initialized: boolean | string;
  auth: boolean;
  progress: Server.Progress[];
  notifications: Server.Notification[];
  sidebar: string;
  badges: Badge;
  offline: boolean;
}

const defaultSite: Site = {
  initialized: false,
  auth: true,
  progress: [],
  notifications: [],
  sidebar: "",
  badges: {
    movies: 0,
    episodes: 0,
    providers: 0,
    status: 0,
  },
  offline: false,
};

const reducer = createReducer(defaultSite, (builder) => {
  builder
    .addCase(siteBootstrap.fulfilled, (state) => {
      state.initialized = true;
    })
    .addCase(siteBootstrap.rejected, (state) => {
      state.initialized = "An Error Occurred When Initializing Bazarr UI";
    })
    .addCase(siteRedirectToAuth, (state) => {
      if (process.env.NODE_ENV !== "development") {
        apis.danger_resetApi("NEED_AUTH");
      }
      state.auth = false;
    })
    .addCase(siteUpdateInitialization, (state, action) => {
      state.initialized = action.payload;
    })
    .addCase(siteAddNotifications, (state, action) => {
      const notifications = uniqBy(
        [...action.payload.reverse(), ...state.notifications],
        (n) => n.id
      );
      state.notifications = notifications;
    })
    .addCase(siteRemoveNotifications, (state, action) => {
      const notifications = [...state.notifications];
      remove(notifications, (n) => n.id === action.payload);
      state.notifications = notifications;
    })
    .addCase(siteAddProgress, (state, action) => {
      const progress = uniqBy(
        [...action.payload.reverse(), ...state.progress],
        (n) => n.id
      );
      state.progress = progress;
    })
    .addCase(siteRemoveProgress, (state, action) => {
      const progress = [...state.progress];
      remove(progress, (n) => n.id === action.payload);
      state.progress = progress;
    })
    .addCase(siteChangeSidebar, (state, action) => {
      state.sidebar = action.payload;
    })
    .addCase(siteUpdateOffline, (state, action) => {
      state.offline = action.payload;
    })
    .addCase(siteUpdateBadges.fulfilled, (state, action) => {
      state.badges = action.payload;
    });
});

export default reducer;
