import {
  SYSTEM_UPDATE_LANGUAGES_LIST,
  SYSTEM_UPDATE_ENABLED_LANGUAGES_LIST,
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  SYSTEM_UPDATE_STATUS,
  SYSTEM_UPDATE_TASKS,
  SYSTEM_UPDATE_LOGS,
  SYSTEM_UPDATE_SETTINGS,
  SYSTEM_UPDATE_RELEASES,
} from "../constants";

import { SystemApi } from "../../apis";
import { createAsyncAction, createCombineAction } from "./utils";

export const systemUpdateLanguagesAll = createCombineAction(() => [
  systemUpdateLanguages(),
  systemUpdateEnabledLanguages(),
  systemUpdateLanguagesProfiles(),
]);

export const systemUpdateLanguages = createAsyncAction(
  SYSTEM_UPDATE_LANGUAGES_LIST,
  () => SystemApi.languages(false)
);

export const systemUpdateEnabledLanguages = createAsyncAction(
  SYSTEM_UPDATE_ENABLED_LANGUAGES_LIST,
  () => SystemApi.languages(true)
);

export const systemUpdateLanguagesProfiles = createAsyncAction(
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  () => SystemApi.languagesProfileList()
);

export const systemUpdateStatus = createAsyncAction(SYSTEM_UPDATE_STATUS, () =>
  SystemApi.status()
);

export const systemUpdateTasks = createAsyncAction(SYSTEM_UPDATE_TASKS, () =>
  SystemApi.getTasks()
);

export const systemUpdateLogs = createAsyncAction(SYSTEM_UPDATE_LOGS, () =>
  SystemApi.logs()
);

export const systemUpdateReleases = createAsyncAction(
  SYSTEM_UPDATE_RELEASES,
  () => SystemApi.releases()
);

export const systemUpdateSettings = createAsyncAction(
  SYSTEM_UPDATE_SETTINGS,
  () => SystemApi.settings()
);

export const systemUpdateSettingsAll = createCombineAction(() => [
  systemUpdateSettings(),
  systemUpdateLanguagesProfiles(),
  systemUpdateEnabledLanguages(),
]);
