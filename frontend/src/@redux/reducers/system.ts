import { handleActions } from "redux-actions";
import {
  SYSTEM_UPDATE_LANGUAGES_LIST,
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  SYSTEM_UPDATE_LOGS,
  SYSTEM_UPDATE_PROVIDERS,
  SYSTEM_UPDATE_RELEASES,
  SYSTEM_UPDATE_SETTINGS,
  SYSTEM_UPDATE_STATUS,
  SYSTEM_UPDATE_TASKS,
} from "../constants";
import { updateAsyncState } from "./mapper";

const reducer = handleActions<ReduxStore.System, any>(
  {
    [SYSTEM_UPDATE_LANGUAGES_LIST]: (state, action) => {
      const languages = updateAsyncState<Array<ApiLanguage>>(action, []);
      const enabledLanguage: AsyncState<ApiLanguage[]> = {
        ...languages,
        data: languages.data.filter((v) => v.enabled),
      };
      const newState = {
        ...state,
        languages,
        enabledLanguage,
      };
      return newState;
    },
    [SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST]: (state, action) => {
      const newState = {
        ...state,
        languagesProfiles: updateAsyncState<Array<Profile.Languages>>(
          action,
          []
        ),
      };
      return newState;
    },
    [SYSTEM_UPDATE_STATUS]: (state, action) => {
      return {
        ...state,
        status: updateAsyncState<System.Status | undefined>(
          action,
          state.status.data
        ),
      };
    },
    [SYSTEM_UPDATE_TASKS]: (state, action) => {
      return {
        ...state,
        tasks: updateAsyncState<Array<System.Task>>(action, state.tasks.data),
      };
    },
    [SYSTEM_UPDATE_PROVIDERS]: (state, action) => {
      return {
        ...state,
        providers: updateAsyncState(action, state.providers.data),
      };
    },
    [SYSTEM_UPDATE_LOGS]: (state, action) => {
      return {
        ...state,
        logs: updateAsyncState(action, state.logs.data),
      };
    },
    [SYSTEM_UPDATE_RELEASES]: (state, action) => {
      return {
        ...state,
        releases: updateAsyncState(action, state.releases.data),
      };
    },
    [SYSTEM_UPDATE_SETTINGS]: (state, action) => {
      return {
        ...state,
        settings: updateAsyncState(action, state.settings.data),
      };
    },
  },
  {
    languages: { updating: true, data: [] },
    enabledLanguage: { updating: true, data: [] },
    languagesProfiles: { updating: true, data: [] },
    status: {
      updating: true,
      data: undefined,
    },
    tasks: {
      updating: true,
      data: [],
    },
    providers: {
      updating: true,
      data: [],
    },
    logs: {
      updating: true,
      data: [],
    },
    releases: {
      updating: true,
      data: [],
    },
    settings: {
      updating: true,
      data: undefined,
    },
  }
);

export default reducer;
