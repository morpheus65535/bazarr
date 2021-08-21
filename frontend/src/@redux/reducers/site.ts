import { createReducer } from "@reduxjs/toolkit";
import { intersectionWith, pullAllWith, remove, sortBy, uniqBy } from "lodash";
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
  progress: Site.Progress[];
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
      if (process.env.NODE_ENV !== "production") {
        apis._resetApi("NEED_AUTH");
      }
      state.auth = false;
    })
    .addCase(siteUpdateInitialization, (state, action) => {
      state.initialized = action.payload;
    });

  builder
    .addCase(siteAddNotifications, (state, action) => {
      state.notifications = uniqBy(
        [...action.payload, ...state.notifications],
        (v) => v.id
      );
      state.notifications = sortBy(state.notifications, (v) => v.id);
    })
    .addCase(siteRemoveNotifications, (state, action) => {
      remove(state.notifications, (n) => n.id === action.payload);
    });

  builder
    .addCase(siteAddProgress, (state, action) => {
      state.progress = uniqBy(
        [...action.payload, ...state.progress],
        (n) => n.id
      );
      state.progress = sortBy(state.progress, (v) => v.id);
    })
    .addCase(siteRemoveProgress.pending, (state, action) => {
      // Mark completed
      intersectionWith(
        state.progress,
        action.meta.arg,
        (l, r) => l.id === r
      ).forEach((v) => {
        v.value = v.count + 1;
      });
    })
    .addCase(siteRemoveProgress.fulfilled, (state, action) => {
      pullAllWith(state.progress, action.payload, (l, r) => l.id === r);
    });

  builder
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
