import { createReducer } from "@reduxjs/toolkit";
import {
  episodesRemoveItems,
  episodeUpdateBy,
  episodeUpdateById,
  seriesRemoveItems,
  seriesRemoveWanted,
  seriesUpdateAll,
  seriesUpdateBlacklist,
  seriesUpdateByRange,
  seriesUpdateHistoryList,
  seriesUpdateList,
  seriesUpdateWantedList,
  seriesUpdateWantedListByRange,
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
    ids: seriesUpdateList,
    removeIds: seriesRemoveItems,
    all: seriesUpdateAll,
  });

  createAsyncEntityReducer(builder, (s) => s.wantedEpisodesList, {
    range: seriesUpdateWantedListByRange,
    ids: seriesUpdateWantedList,
    removeIds: seriesRemoveWanted,
  });

  createAsyncListReducer(builder, (s) => s.historyList, "raw_timestamp", {
    all: seriesUpdateHistoryList,
  });

  createAsyncListReducer(builder, (s) => s.blacklist, "timestamp", {
    all: seriesUpdateBlacklist,
  });

  createAsyncListReducer(builder, (s) => s.episodeList, "sonarrEpisodeId", {
    ids: episodeUpdateBy,
  });

  createAsyncListReducer(builder, (s) => s.episodeList, "sonarrEpisodeId", {
    ids: episodeUpdateById,
    removeIds: episodesRemoveItems,
  });
});

export default reducer;
