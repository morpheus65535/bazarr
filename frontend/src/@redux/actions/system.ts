import {
  UPDATE_LANGUAGES_LIST,
  UPDATE_SYSTEM_STATUS,
  UPDATE_SYSTEM_TASKS,
  UPDATE_SYSTEM_LOGS,
  UPDATE_SYSTEM_SETTINGS,
} from "../constants";

import { SystemApi } from "../../apis";
import { createAsyncAction } from "./utils";

export const updateLanguagesList = createAsyncAction(
  UPDATE_LANGUAGES_LIST,
  (enabled: boolean = false) => SystemApi.languages(enabled)
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
