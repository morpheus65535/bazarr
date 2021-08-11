import { createReducer } from "@reduxjs/toolkit";
import {
  episodesMarkBlacklistDirty,
  episodesMarkDirtyById,
  episodesMarkHistoryDirty,
  episodesRemoveById,
  episodesUpdateBlacklist,
  episodesUpdateHistory,
  episodeUpdateById,
  episodeUpdateBySeriesId,
  seriesMarkDirtyById,
  seriesMarkWantedDirtyById,
  seriesRemoveById,
  seriesRemoveWantedById,
  seriesUpdateAll,
  seriesUpdateById,
  seriesUpdateByRange,
  seriesUpdateWantedById,
  seriesUpdateWantedByRange,
} from "../actions";
import { AsyncReducer, AsyncUtility } from "../utils/async";
import {
  createAsyncEntityReducer,
  createAsyncItemReducer,
  createAsyncListReducer,
} from "../utils/factory";

interface Series {
  seriesList: Async.Entity<Item.Series>;
  wantedEpisodesList: Async.Entity<Wanted.Episode>;
  episodeList: Async.List<Item.Episode>;
  historyList: Async.Item<History.Episode[]>;
  blacklist: Async.Item<Blacklist.Episode[]>;
}

const defaultSeries: Series = {
  seriesList: AsyncUtility.getDefaultEntity("sonarrSeriesId"),
  wantedEpisodesList: AsyncUtility.getDefaultEntity("sonarrEpisodeId"),
  episodeList: AsyncUtility.getDefaultList("sonarrEpisodeId"),
  historyList: AsyncUtility.getDefaultItem(),
  blacklist: AsyncUtility.getDefaultItem(),
};

const reducer = createReducer(defaultSeries, (builder) => {
  createAsyncEntityReducer(builder, (s) => s.seriesList, {
    range: seriesUpdateByRange,
    ids: seriesUpdateById,
    removeIds: seriesRemoveById,
    all: seriesUpdateAll,
    dirty: seriesMarkDirtyById,
  });

  builder.addCase(seriesMarkDirtyById, (state, action) => {
    const series = state.seriesList;
    const dirtyIds = action.payload.map(String);

    AsyncReducer.markDirty(series, dirtyIds);

    // Update episode list
    const episodes = state.episodeList;
    const dirtyIdsSet = new Set(dirtyIds);
    const dirtyEpisodeIds = episodes.content
      .filter((v) => dirtyIdsSet.has(v.sonarrSeriesId.toString()))
      .map((v) => String(v.sonarrEpisodeId));

    AsyncReducer.markDirty(episodes, dirtyEpisodeIds);
  });

  createAsyncEntityReducer(builder, (s) => s.wantedEpisodesList, {
    range: seriesUpdateWantedByRange,
    ids: seriesUpdateWantedById,
    removeIds: seriesRemoveWantedById,
    dirty: seriesMarkWantedDirtyById,
  });

  createAsyncItemReducer(builder, (s) => s.historyList, {
    all: episodesUpdateHistory,
    dirty: episodesMarkHistoryDirty,
  });

  createAsyncItemReducer(builder, (s) => s.blacklist, {
    all: episodesUpdateBlacklist,
    dirty: episodesMarkBlacklistDirty,
  });

  createAsyncListReducer(builder, (s) => s.episodeList, {
    ids: episodeUpdateBySeriesId,
  });

  createAsyncListReducer(builder, (s) => s.episodeList, {
    ids: episodeUpdateById,
    removeIds: episodesRemoveById,
    dirty: episodesMarkDirtyById,
  });
});

export default reducer;
