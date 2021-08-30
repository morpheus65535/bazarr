import { createAction, createAsyncThunk } from "@reduxjs/toolkit";
import { MoviesApi } from "../../apis";

export const movieUpdateByRange = createAsyncThunk(
  "movies/update/range",
  async (params: Parameter.Range) => {
    const response = await MoviesApi.moviesBy(params);
    return response;
  }
);

export const movieUpdateById = createAsyncThunk(
  "movies/update/id",
  async (ids: number[]) => {
    const response = await MoviesApi.movies(ids);
    return response;
  }
);

export const movieUpdateAll = createAsyncThunk(
  "movies/update/all",
  async () => {
    const response = await MoviesApi.movies();
    return response;
  }
);

export const movieRemoveById = createAction<number[]>("movies/remove");

export const movieMarkDirtyById = createAction<number[]>(
  "movies/mark_dirty/id"
);

export const movieUpdateWantedById = createAsyncThunk(
  "movies/wanted/update/id",
  async (ids: number[]) => {
    const response = await MoviesApi.wantedBy(ids);
    return response;
  }
);

export const movieRemoveWantedById = createAction<number[]>(
  "movies/wanted/remove/id"
);

export const movieResetWanted = createAction("movies/wanted/reset");

export const movieMarkWantedDirtyById = createAction<number[]>(
  "movies/wanted/mark_dirty/id"
);

export const movieUpdateWantedByRange = createAsyncThunk(
  "movies/wanted/update/range",
  async (params: Parameter.Range) => {
    const response = await MoviesApi.wanted(params);
    return response;
  }
);

export const movieUpdateHistoryByRange = createAsyncThunk(
  "movies/history/update/range",
  async (params: Parameter.Range) => {
    const response = await MoviesApi.history(params);
    return response;
  }
);

export const movieMarkHistoryDirty = createAction<number[]>(
  "movies/history/mark_dirty"
);

export const movieResetHistory = createAction("movie/history/reset");

export const movieUpdateBlacklist = createAsyncThunk(
  "movies/blacklist/update",
  async () => {
    const response = await MoviesApi.blacklist();
    return response;
  }
);

export const movieMarkBlacklistDirty = createAction(
  "movies/blacklist/mark_dirty"
);
