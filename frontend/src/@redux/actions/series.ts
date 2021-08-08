import { createAction, createAsyncThunk } from "@reduxjs/toolkit";
import { EpisodesApi, SeriesApi } from "../../apis";

export const seriesUpdateWantedById = createAsyncThunk(
  "series/wanted/update",
  async (episodeid: number[]) => {
    const response = await EpisodesApi.wantedBy(episodeid);
    return response;
  }
);

export const seriesUpdateWantedByRange = createAsyncThunk(
  "series/wanted/update/range",
  async (params: Parameter.Range) => {
    const response = await EpisodesApi.wanted(params);
    return response;
  }
);

export const seriesRemoveWantedById = createAction<number[]>(
  "series/wanted/remove"
);

export const seriesRemoveById = createAction<number[]>("series/remove");

export const episodesRemoveById = createAction<number[]>("episodes/remove");

export const seriesUpdateById = createAsyncThunk(
  "series/update",
  async (ids: number[]) => {
    const response = await SeriesApi.series(ids);
    return response;
  }
);

export const seriesUpdateAll = createAsyncThunk(
  "series/update/all",
  async () => {
    const response = await SeriesApi.series();
    return response;
  }
);

export const seriesUpdateByRange = createAsyncThunk(
  "series/update/range",
  async (params: Parameter.Range) => {
    const response = await SeriesApi.seriesBy(params);
    return response;
  }
);

export const episodeUpdateBySeriesId = createAsyncThunk(
  "episodes/update/series_id",
  async (seriesid: number[]) => {
    const response = await EpisodesApi.bySeriesId(seriesid);
    return response;
  }
);

export const episodeUpdateByEpisodeId = createAsyncThunk(
  "episodes/update/episodes_id",
  async (episodeid: number[]) => {
    const response = await EpisodesApi.byEpisodeId(episodeid);
    return response;
  }
);

export const seriesUpdateHistory = createAsyncThunk(
  "series/history/update",
  async () => {
    const response = await EpisodesApi.history();
    return response;
  }
);

export const seriesUpdateBlacklist = createAsyncThunk(
  "series/blacklist/update",
  async () => {
    const response = await EpisodesApi.blacklist();
    return response;
  }
);
