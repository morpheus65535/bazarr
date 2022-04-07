import { createReducer } from "@reduxjs/toolkit";
import apis from "../../../apis/queries/client";
import { isProdEnv } from "../../../utilities";
import {
  setOfflineStatus,
  setSidebar,
  setSiteStatus,
  setUnauthenticated,
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
    .addCase(setSidebar, (state, action) => {
      state.showSidebar = action.payload;
    })
    .addCase(setOfflineStatus, (state, action) => {
      state.offline = action.payload;
    });
});

export default reducer;
