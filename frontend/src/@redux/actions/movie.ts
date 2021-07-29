import { createAction, createAsyncThunk } from "@reduxjs/toolkit";
import { MoviesApi } from "../../apis";

export const movieUpdateByRange = createAsyncThunk(
  "movies/update/range",
  async (params: ReduxStore.ByRangePayload) => {
    const { start, length } = params;
    const response = await MoviesApi.moviesBy(start, length);
    return response;
  }
);

export const movieUpdateList = createAsyncThunk(
  "movies/update/movie_id",
  async (ids?: number[]) => {
    const response = await MoviesApi.movies(ids);
    return response;
  }
);

export const movieRemoveItems = createAction<number[]>("movies/remove");

export const movieUpdateWantedList = createAsyncThunk(
  "movies/wanted/update/movie_id",
  async (ids: number[]) => {
    const response = await MoviesApi.wantedBy(ids);
    return response;
  }
);

export const movieRemoveWantedItems = createAction<number[]>(
  "movies/wanted/remove"
);

export const movieUpdateWantedByRange = createAsyncThunk(
  "movies/wanted/update/range",
  async (params: ReduxStore.ByRangePayload) => {
    const { start, length } = params;
    const response = await MoviesApi.wanted(start, length);
    return response;
  }
);

export const movieUpdateHistoryList = createAsyncThunk(
  "movies/history/update",
  async () => {
    const response = await MoviesApi.history();
    return response;
  }
);

export const movieUpdateBlacklist = createAsyncThunk(
  "movies/blacklist/update",
  async () => {
    const response = await MoviesApi.blacklist();
    return response;
  }
);
