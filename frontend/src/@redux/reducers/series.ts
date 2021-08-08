import { createReducer } from "@reduxjs/toolkit";
import {
  episodesRemoveById,
  episodeUpdateByEpisodeId,
  episodeUpdateBySeriesId,
  seriesRemoveById,
  seriesRemoveWantedById,
  seriesUpdateAll,
  seriesUpdateBlacklist,
  seriesUpdateById,
  seriesUpdateByRange,
  seriesUpdateHistory,
  seriesUpdateWantedById,
  seriesUpdateWantedByRange,
} from "../actions";
import { AsyncUtility } from "../utils/async";
import {
  createAsyncEntityReducer,
  createAsyncListReducer,
} from "../utils/factory";

interface Series {
  seriesList: Async.Entity<Item.Series>;
  wantedEpisodesList: Async.Entity<Wanted.Episode>;
  episodeList: Async.List<Item.Episode>;
  historyList: Async.List<History.Episode>;
  blacklist: Async.List<Blacklist.Episode>;
}

const defaultSeries: Series = {
  seriesList: AsyncUtility.getDefaultEntity("sonarrSeriesId"),
  wantedEpisodesList: AsyncUtility.getDefaultEntity("sonarrEpisodeId"),
  episodeList: AsyncUtility.getDefaultList(),
  historyList: AsyncUtility.getDefaultList(),
  blacklist: AsyncUtility.getDefaultList(),
};

const reducer = createReducer(defaultSeries, (builder) => {
  createAsyncEntityReducer(builder, (s) => s.seriesList, {
    range: seriesUpdateByRange,
    ids: seriesUpdateById,
    removeIds: seriesRemoveById,
    all: seriesUpdateAll,
  });

  createAsyncEntityReducer(builder, (s) => s.wantedEpisodesList, {
    range: seriesUpdateWantedByRange,
    ids: seriesUpdateWantedById,
    removeIds: seriesRemoveWantedById,
  });

  createAsyncListReducer(builder, (s) => s.historyList, "raw_timestamp", {
    all: seriesUpdateHistory,
  });

  createAsyncListReducer(builder, (s) => s.blacklist, "timestamp", {
    all: seriesUpdateBlacklist,
  });

  createAsyncListReducer(builder, (s) => s.episodeList, "sonarrEpisodeId", {
    ids: episodeUpdateBySeriesId,
  });

  createAsyncListReducer(builder, (s) => s.episodeList, "sonarrEpisodeId", {
    ids: episodeUpdateByEpisodeId,
    removeIds: episodesRemoveById,
  });
});

export default reducer;
