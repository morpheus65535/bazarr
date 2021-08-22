import { createAction, createAsyncThunk } from "@reduxjs/toolkit";
import { BadgesApi } from "../../apis";
import { waitFor } from "../../utilites";
import { systemUpdateAllSettings } from "./system";

export const siteBootstrap = createAsyncThunk(
  "site/bootstrap",
  (_: undefined, { dispatch }) => {
    return Promise.all([
      dispatch(systemUpdateAllSettings()),
      dispatch(siteUpdateBadges()),
    ]);
  }
);

export const siteUpdateInitialization = createAction<string | true>(
  "site/initialization/update"
);

export const siteRedirectToAuth = createAction("site/redirect_auth");

export const siteAddNotifications = createAction<Server.Notification[]>(
  "site/notifications/add"
);

export const siteRemoveNotifications = createAction<string>(
  "site/notifications/remove"
);

export const siteAddProgress =
  createAction<Site.Progress[]>("site/progress/add");

export const siteUpdateProgressCount = createAction<{
  id: string;
  count: number;
}>("site/progress/update_count");

export const siteRemoveProgress = createAsyncThunk(
  "site/progress/remove",
  async (ids: string[]) => {
    await waitFor(3 * 1000);
    return ids;
  }
);

export const siteUpdateNotifier = createAction<string>(
  "site/progress/update_notifier"
);

export const siteChangeSidebar = createAction<string>("site/sidebar/update");

export const siteUpdateOffline = createAction<boolean>("site/offline/update");

export const siteUpdateBadges = createAsyncThunk(
  "site/badges/update",
  async () => {
    const response = await BadgesApi.all();
    return response;
  }
);
