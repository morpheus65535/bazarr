import { createReducer } from "@reduxjs/toolkit";
import {
  providerUpdateList,
  systemMarkTasksDirty,
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
  createAsyncListReducer(builder, (s) => s.languages, "code2", {
    all: systemUpdateLanguages,
  });

  createAsyncListReducer(builder, (s) => s.languagesProfiles, "profileId", {
    all: systemUpdateLanguagesProfiles,
  });
  createAsyncItemReducer(builder, { all: systemUpdateStatus }, (s) => s.status);
  createAsyncItemReducer(
    builder,
    { all: systemUpdateSettings },
    (s) => s.settings
  );
  createAsyncListReducer(builder, (s) => s.releases, "date", {
    all: systemUpdateReleases,
  });
  createAsyncListReducer(builder, (s) => s.logs, "timestamp", {
    all: systemUpdateLogs,
  });

  createAsyncListReducer(builder, (s) => s.health, "object", {
    all: systemUpdateHealth,
  });

  createAsyncListReducer(builder, (s) => s.tasks, "job_id", {
    all: systemUpdateTasks,
    allDirty: systemMarkTasksDirty,
  });

  createAsyncListReducer(builder, (s) => s.providers, "name", {
    all: providerUpdateList,
  });
});

export default reducer;
