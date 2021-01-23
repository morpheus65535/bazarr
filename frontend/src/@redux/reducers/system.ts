import {
  UPDATE_ALL_LANGUAGES_LIST,
  UPDATE_ENABLED_LANGUAGES_LIST,
  UPDATE_LANGUAGES_PROFILE_LIST,
  UPDATE_SYSTEM_STATUS,
  UPDATE_SYSTEM_TASKS,
  UPDATE_PROVIDER_LIST,
  UPDATE_SYSTEM_LOGS,
  UPDATE_SYSTEM_SETTINGS,
} from "../constants";
import { mapToAsyncState } from "./mapper";

import { handleActions } from "redux-actions";

const checkInitialize = (state: SystemState): boolean => {
  return (
    state.initialized ||
    (!state.languages.updating &&
      !state.enabledLanguage.updating &&
      !state.languagesProfiles.updating)
  );
};

const reducer = handleActions<SystemState, any>(
  {
    [UPDATE_ALL_LANGUAGES_LIST]: {
      next(state, action) {
        const newState = {
          ...state,
          languages: mapToAsyncState<Array<Language>>(action, []),
        };
        newState.initialized = checkInitialize(newState);
        return newState;
      },
    },
    [UPDATE_ENABLED_LANGUAGES_LIST]: {
      next(state, action) {
        const newState = {
          ...state,
          enabledLanguage: mapToAsyncState<Array<Language>>(action, []),
        };
        newState.initialized = checkInitialize(newState);
        return newState;
      },
    },
    [UPDATE_LANGUAGES_PROFILE_LIST]: {
      next(state, action) {
        const newState = {
          ...state,
          languagesProfiles: mapToAsyncState<Array<LanguagesProfile>>(
            action,
            []
          ),
        };
        newState.initialized = checkInitialize(newState);
        return newState;
      },
    },
    [UPDATE_SYSTEM_STATUS]: {
      next(state, action) {
        return {
          ...state,
          status: mapToAsyncState<SystemStatusResult | undefined>(
            action,
            state.status.items
          ),
        };
      },
    },
    [UPDATE_SYSTEM_TASKS]: {
      next(state, action) {
        return {
          ...state,
          tasks: mapToAsyncState<Array<SystemTaskResult>>(
            action,
            state.tasks.items
          ),
        };
      },
    },
    [UPDATE_PROVIDER_LIST]: {
      next(state, action) {
        return {
          ...state,
          providers: mapToAsyncState(action, state.providers.items),
        };
      },
    },
    [UPDATE_SYSTEM_LOGS]: {
      next(state, action) {
        return {
          ...state,
          logs: mapToAsyncState(action, state.logs.items),
        };
      },
    },
    [UPDATE_SYSTEM_SETTINGS]: {
      next(state, action) {
        return {
          ...state,
          settings: mapToAsyncState(action, state.settings.items),
        };
      },
    },
  },
  {
    initialized: false,
    languages: { updating: true, items: [] },
    enabledLanguage: { updating: true, items: [] },
    languagesProfiles: { updating: true, items: [] },
    status: {
      updating: true,
      items: undefined,
    },
    tasks: {
      updating: true,
      items: [],
    },
    providers: {
      updating: true,
      items: [],
    },
    logs: {
      updating: true,
      items: [],
    },
    settings: {
      updating: true,
      items: undefined,
    },
  }
);

export default reducer;
