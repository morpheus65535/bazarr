import { createAction, createAsyncThunk } from "@reduxjs/toolkit";
import { EpisodesApi, SeriesApi } from "../../apis";

export const seriesUpdateWantedList = createAsyncThunk(
  "series/wanted/update",
  async (episodeid: number[]) => {
    const response = await EpisodesApi.wantedBy(episodeid);
    return response;
  }
);

export const seriesUpdateWantedListByRange = createAsyncThunk(
  "series/wanted/update/range",
  async (params: Parameter.Range) => {
    const response = await EpisodesApi.wanted(params);
    return response;
  }
);

export const seriesRemoveWanted = createAction<number[]>(
  "series/wanted/remove"
);

export const seriesRemoveItems = createAction<number[]>("series/remove");

export const episodesRemoveItems = createAction<number[]>("episodes/remove");

export const seriesUpdateList = createAsyncThunk(
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

export const episodeUpdateBy = createAsyncThunk(
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

export const seriesUpdateHistoryList = createAsyncThunk(
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
