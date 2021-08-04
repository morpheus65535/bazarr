import { createReducer } from "@reduxjs/toolkit";
import {
  providerUpdateList,
  systemUpdateHealth,
  systemUpdateLanguages,
  systemUpdateLanguagesProfiles,
  systemUpdateLogs,
  systemUpdateReleases,
  systemUpdateSettings,
  systemUpdateStatus,
  systemUpdateTasks,
} from "../actions";
import { AsyncUtility } from "../utils/async";
import {
  createAsyncItemReducer,
  createAsyncListReducer,
} from "../utils/factory";

interface System {
  languages: Async.List<Language.Server>;
  languagesProfiles: Async.List<Language.Profile>;
  status: Async.Item<System.Status>;
  health: Async.List<System.Health>;
  tasks: Async.List<System.Task>;
  providers: Async.List<System.Provider>;
  logs: Async.List<System.Log>;
  releases: Async.List<ReleaseInfo>;
  settings: Async.Item<Settings>;
}

const defaultSystem: System = {
  languages: AsyncUtility.getDefaultList(),
  languagesProfiles: AsyncUtility.getDefaultList(),
  status: AsyncUtility.getDefaultItem(),
  health: AsyncUtility.getDefaultList(),
  tasks: AsyncUtility.getDefaultList(),
  providers: AsyncUtility.getDefaultList(),
  logs: AsyncUtility.getDefaultList(),
  releases: AsyncUtility.getDefaultList(),
  settings: AsyncUtility.getDefaultItem(),
};

const reducer = createReducer(defaultSystem, (builder) => {
  createAsyncListReducer(builder, systemUpdateLanguages, (s) => s.languages);

  createAsyncListReducer(
    builder,
    systemUpdateLanguagesProfiles,
    (s) => s.languagesProfiles
  );
  createAsyncItemReducer(builder, systemUpdateStatus, (s) => s.status);
  createAsyncItemReducer(builder, systemUpdateSettings, (s) => s.settings);
  createAsyncListReducer(builder, systemUpdateReleases, (s) => s.releases);
  createAsyncListReducer(builder, systemUpdateLogs, (s) => s.logs);

  createAsyncListReducer(builder, systemUpdateHealth, (s) => s.health);
  createAsyncListReducer(builder, systemUpdateTasks, (s) => s.tasks);
  createAsyncListReducer(builder, providerUpdateList, (s) => s.providers);
});

export default reducer;
