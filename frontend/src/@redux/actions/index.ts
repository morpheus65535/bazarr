import { createAction, createAsyncThunk } from "@reduxjs/toolkit";
import { waitFor } from "../../utilities";

export const setSiteStatus = createAction<Site.Status>("site/status/update");

export const setUnauthenticated = createAction("site/unauthenticated");

export const setOfflineStatus = createAction<boolean>("site/offline/update");

export const addNotifications = createAction<Server.Notification[]>(
  "site/notifications/add"
);

export const removeNotification = createAction<string>(
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

export const setSidebar = createAction<boolean>("site/sidebar/update");
