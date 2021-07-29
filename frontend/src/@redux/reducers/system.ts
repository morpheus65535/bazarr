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
import { defaultAS } from "../utils";
import { createAsyncStateReducer } from "../utils/factory";

interface System {
  languages: AsyncState<Array<Language>>;
  enabledLanguage: AsyncState<Array<Language>>;
  languagesProfiles: AsyncState<Array<Profile.Languages>>;
  status: AsyncState<System.Status | undefined>;
  health: AsyncState<Array<System.Health>>;
  tasks: AsyncState<Array<System.Task>>;
  providers: AsyncState<Array<System.Provider>>;
  logs: AsyncState<Array<System.Log>>;
  releases: AsyncState<Array<ReleaseInfo>>;
  settings: AsyncState<Settings | undefined>;
}

const defaultSystem: System = {
  languages: defaultAS([]),
  enabledLanguage: defaultAS([]),
  languagesProfiles: defaultAS([]),
  status: defaultAS(undefined),
  health: defaultAS([]),
  tasks: defaultAS([]),
  providers: defaultAS([]),
  logs: defaultAS([]),
  releases: defaultAS([]),
  settings: defaultAS(undefined),
};

const reducer = createReducer(defaultSystem, (builder) => {
  createAsyncStateReducer(
    builder,
    systemUpdateLanguages,
    (s) => s.languages,
    (state, action) => {
      const enabled = action.payload.filter((v) => v.enabled);
      const languages = action.payload as Language[];
      state.enabledLanguage.state = "succeeded";
      state.enabledLanguage.data = enabled;

      state.languages.state = "succeeded";
      state.languages.data = languages;
    }
  );

  createAsyncStateReducer(
    builder,
    systemUpdateLanguagesProfiles,
    (s) => s.languagesProfiles
  );
  createAsyncStateReducer(builder, systemUpdateHealth, (s) => s.health);
  createAsyncStateReducer(builder, systemUpdateStatus, (s) => s.status);
  createAsyncStateReducer(builder, systemUpdateLogs, (s) => s.logs);
  createAsyncStateReducer(builder, systemUpdateTasks, (s) => s.tasks);
  createAsyncStateReducer(builder, providerUpdateList, (s) => s.providers);
  createAsyncStateReducer(builder, systemUpdateReleases, (s) => s.releases);
  createAsyncStateReducer(builder, systemUpdateSettings, (s) => s.settings);
});

export default reducer;
