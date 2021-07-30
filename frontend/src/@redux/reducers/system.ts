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
import { Async } from "../types/async";
import { defaultAS } from "../utils";
import { AsyncUtility } from "../utils/async";
import {
  createAsyncItemReducer,
  createAsyncStateReducer,
} from "../utils/factory";

interface System {
  languages: AsyncState<Language.Server[]>;
  languagesProfiles: AsyncState<Language.Profile[]>;
  status: Async.Item<System.Status>;
  health: AsyncState<System.Health[]>;
  tasks: AsyncState<System.Task[]>;
  providers: AsyncState<System.Provider[]>;
  logs: AsyncState<System.Log[]>;
  releases: AsyncState<ReleaseInfo[]>;
  settings: Async.Item<Settings>;
}

const defaultSystem: System = {
  languages: defaultAS([]),
  languagesProfiles: defaultAS([]),
  status: AsyncUtility.getDefaultItem(),
  health: defaultAS([]),
  tasks: defaultAS([]),
  providers: defaultAS([]),
  logs: defaultAS([]),
  releases: defaultAS([]),
  settings: AsyncUtility.getDefaultItem(),
};

const reducer = createReducer(defaultSystem, (builder) => {
  createAsyncStateReducer(builder, systemUpdateLanguages, (s) => s.languages);

  createAsyncStateReducer(
    builder,
    systemUpdateLanguagesProfiles,
    (s) => s.languagesProfiles
  );
  createAsyncItemReducer(builder, systemUpdateStatus, (s) => s.status);
  createAsyncItemReducer(builder, systemUpdateSettings, (s) => s.settings);

  createAsyncStateReducer(builder, systemUpdateHealth, (s) => s.health);
  createAsyncStateReducer(builder, systemUpdateLogs, (s) => s.logs);
  createAsyncStateReducer(builder, systemUpdateTasks, (s) => s.tasks);
  createAsyncStateReducer(builder, providerUpdateList, (s) => s.providers);
  createAsyncStateReducer(builder, systemUpdateReleases, (s) => s.releases);
});

export default reducer;
