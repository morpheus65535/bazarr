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
  "movies/update/movie_id",
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

export const movieUpdateWantedById = createAsyncThunk(
  "movies/wanted/update/movie_id",
  async (ids: number[]) => {
    const response = await MoviesApi.wantedBy(ids);
    return response;
  }
);

export const movieRemoveWantedById = createAction<number[]>(
  "movies/wanted/remove"
);

export const movieUpdateWantedByRange = createAsyncThunk(
  "movies/wanted/update/range",
  async (params: Parameter.Range) => {
    const response = await MoviesApi.wanted(params);
    return response;
  }
);

export const movieUpdateHistory = createAsyncThunk(
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
