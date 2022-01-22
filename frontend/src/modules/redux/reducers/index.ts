import { createReducer } from "@reduxjs/toolkit";
import { intersectionWith, pullAllWith, remove, sortBy, uniqBy } from "lodash";
import apis from "../../../apis/queries/client";
import { isProdEnv } from "../../../utilities";
import {
  addNotifications,
  removeNotification,
  setOfflineStatus,
  setSidebar,
  setSiteStatus,
  setUnauthenticated,
  siteAddProgress,
  siteRemoveProgress,
  siteUpdateNotifier,
  siteUpdateProgressCount,
} from "../actions";

interface Site {
  // Initialization state or error message
  status: Site.Status;
  offline: boolean;
  progress: Site.Progress[];
  notifier: {
    content: string | null;
    timestamp: string;
  };
  notifications: Server.Notification[];
  showSidebar: boolean;
}

const defaultSite: Site = {
  status: "uninitialized",
  progress: [],
  notifier: {
    content: null,
    timestamp: String(Date.now()),
  },
  notifications: [],
  showSidebar: false,
  offline: false,
};

const reducer = createReducer(defaultSite, (builder) => {
  builder
    .addCase(setUnauthenticated, (state) => {
      if (!isProdEnv) {
        apis._resetApi("NEED_AUTH");
      }
      state.status = "unauthenticated";
    })
    .addCase(setSiteStatus, (state, action) => {
      state.status = action.payload;
    });

  builder
    .addCase(addNotifications, (state, action) => {
      state.notifications = uniqBy(
        [...action.payload, ...state.notifications],
        (v) => v.id
      );
      state.notifications = sortBy(state.notifications, (v) => v.id);
    })
    .addCase(removeNotification, (state, action) => {
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
    })
    .addCase(siteUpdateProgressCount, (state, action) => {
      const { id, count } = action.payload;
      const progress = state.progress.find((v) => v.id === id);
      if (progress) {
        progress.count = count;
      }
    });

  builder.addCase(siteUpdateNotifier, (state, action) => {
    state.notifier.content = action.payload;
    state.notifier.timestamp = String(Date.now());
  });

  builder
    .addCase(setSidebar, (state, action) => {
      state.showSidebar = action.payload;
    })
    .addCase(setOfflineStatus, (state, action) => {
      state.offline = action.payload;
    });
});

export default reducer;
