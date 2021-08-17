import { createAction, createAsyncThunk } from "@reduxjs/toolkit";
import { EpisodesApi, SeriesApi } from "../../apis";

export const seriesUpdateWantedById = createAsyncThunk(
  "series/wanted/update/id",
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
  "series/wanted/remove/id"
);

export const seriesMarkWantedDirtyById = createAction<number[]>(
  "series/wanted/mark_dirty/episode_id"
);

export const seriesRemoveById = createAction<number[]>("series/remove");

export const seriesMarkDirtyById = createAction<number[]>(
  "series/mark_dirty/id"
);

export const seriesUpdateById = createAsyncThunk(
  "series/update/id",
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

export const episodesRemoveById = createAction<number[]>("episodes/remove");

export const episodesMarkDirtyById = createAction<number[]>(
  "episodes/mark_dirty/id"
);

export const episodeUpdateBySeriesId = createAsyncThunk(
  "episodes/update/series_id",
  async (seriesid: number[]) => {
    const response = await EpisodesApi.bySeriesId(seriesid);
    return response;
  }
);

export const episodeUpdateById = createAsyncThunk(
  "episodes/update/episodes_id",
  async (episodeid: number[]) => {
    const response = await EpisodesApi.byEpisodeId(episodeid);
    return response;
  }
);

export const episodesUpdateHistoryByRange = createAsyncThunk(
  "episodes/history/update/range",
  async (param: Parameter.Range) => {
    const response = await EpisodesApi.history(param);
    return response;
  }
);

export const episodesMarkHistoryDirty = createAction<number[]>(
  "episodes/history/update"
);

export const episodesUpdateBlacklist = createAsyncThunk(
  "episodes/blacklist/update",
  async () => {
    const response = await EpisodesApi.blacklist();
    return response;
  }
);

export const episodesMarkBlacklistDirty = createAction(
  "episodes/blacklist/update"
);
