import { createAction, createAsyncThunk } from "@reduxjs/toolkit";
import { BadgesApi } from "../../apis";

// export const bootstrap = createCallbackAction(
//   () => [systemUpdateLanguagesAll(), systemUpdateSettings(), badgeUpdateAll()],
//   () => siteUpdateInitialization(true),
//   () => siteUpdateInitialization(null)
// );

export const siteUpdateInitialization = createAction<string | null | true>(
  "site/initialization/update"
);

export const siteRedirectToAuth = createAction("site/redirect_auth");

export const siteAddNotifications = createAction<Server.Notification[]>(
  "site/notifications/add"
);

export const siteRemoveNotifications = createAction<string>(
  "site/notifications/remove"
);

export const siteAddProgress = createAction<Server.Progress[]>(
  "site/progress/add"
);

export const siteRemoveProgress = createAction<string>("site/progress/remove");

export const siteChangeSidebar = createAction<string>("site/sidebar/update");

export const siteUpdateOffline = createAction<boolean>("site/offline/update");

export const siteUpdateBadges = createAsyncThunk(
  "site/badges/update",
  async () => {
    const response = await BadgesApi.all();
    return response;
  }
);
