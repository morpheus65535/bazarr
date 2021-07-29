import { createAsyncThunk } from "@reduxjs/toolkit";
import { ProvidersApi, SystemApi } from "../../apis";

export const systemUpdateLanguages = createAsyncThunk(
  "system/languages/update",
  async () => {
    const response = await SystemApi.languages();
    return response;
  }
);

export const systemUpdateLanguagesProfiles = createAsyncThunk(
  "system/languages/profile/update",
  async () => {
    const response = await SystemApi.languagesProfileList();
    return response;
  }
);

export const systemUpdateStatus = createAsyncThunk(
  "system/status/update",
  async () => {
    const response = await SystemApi.status();
    return response;
  }
);

export const systemUpdateHealth = createAsyncThunk(
  "system/health/update",
  async () => {
    const response = await SystemApi.health();
    return response;
  }
);

export const systemUpdateTasks = createAsyncThunk(
  "system/tasks/update",
  async () => {
    const response = await SystemApi.tasks();
    return response;
  }
);

export const systemUpdateLogs = createAsyncThunk(
  "system/logs/update",
  async () => {
    const response = await SystemApi.logs();
    return response;
  }
);

export const systemUpdateReleases = createAsyncThunk(
  "system/releases/update",
  async () => {
    const response = await SystemApi.releases();
    return response;
  }
);

export const systemUpdateSettings = createAsyncThunk(
  "system/settings/update",
  async () => {
    const response = await SystemApi.settings();
    return response;
  }
);

export const providerUpdateList = createAsyncThunk(
  "providers/update",
  async () => {
    const response = await ProvidersApi.providers();
    return response;
  }
);
