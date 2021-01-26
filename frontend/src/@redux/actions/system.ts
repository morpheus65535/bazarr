import {
  UPDATE_ALL_LANGUAGES_LIST,
  UPDATE_ENABLED_LANGUAGES_LIST,
  UPDATE_LANGUAGES_PROFILE_LIST,
  UPDATE_SYSTEM_STATUS,
  UPDATE_SYSTEM_TASKS,
  UPDATE_SYSTEM_LOGS,
  UPDATE_SYSTEM_SETTINGS,
} from "../constants";

import { SystemApi } from "../../apis";
import { createAsyncAction, createCombineAction } from "./utils";

export const updateLanguagesList = createCombineAction(() => [
  updateAllLanguages(),
  updateEnabledLanguages(),
  updateLanguagesProfileList(),
]);

export const updateAllLanguages = createAsyncAction(
  UPDATE_ALL_LANGUAGES_LIST,
  () => SystemApi.languages(false)
);

export const updateEnabledLanguages = createAsyncAction(
  UPDATE_ENABLED_LANGUAGES_LIST,
  () => SystemApi.languages(true)
);

export const updateLanguagesProfileList = createAsyncAction(
  UPDATE_LANGUAGES_PROFILE_LIST,
  () => SystemApi.languagesProfileList()
);

export const UpdateSystemStatus = createAsyncAction(UPDATE_SYSTEM_STATUS, () =>
  SystemApi.status()
);

export const UpdateSystemTasks = createAsyncAction(UPDATE_SYSTEM_TASKS, () =>
  SystemApi.getTasks()
);

export const UpdateSystemLogs = createAsyncAction(UPDATE_SYSTEM_LOGS, () =>
  SystemApi.logs()
);

export const UpdateSystemSettings = createAsyncAction(
  UPDATE_SYSTEM_SETTINGS,
  () => SystemApi.settings()
);

export const UpdateSettingsRelative = createCombineAction(() => [
  UpdateSystemSettings(),
  updateLanguagesProfileList(),
  updateEnabledLanguages(),
]);
