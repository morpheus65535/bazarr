import { createReducer } from "@reduxjs/toolkit";
import {
  episodesRemoveItems,
  episodeUpdateBy,
  episodeUpdateById,
  seriesRemoveItems,
  seriesRemoveWanted,
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
  createAsyncListIdReducer,
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
  createAsyncEntityReducer(
    builder,
    seriesUpdateByRange,
    seriesUpdateList,
    seriesRemoveItems,
    (s) => s.seriesList
  );

  createAsyncEntityReducer(
    builder,
    seriesUpdateWantedListByRange,
    seriesUpdateWantedList,
    seriesRemoveWanted,
    (s) => s.wantedEpisodesList
  );

  createAsyncListReducer(
    builder,
    seriesUpdateHistoryList,
    (s) => s.historyList
  );

  createAsyncListReducer(builder, seriesUpdateBlacklist, (s) => s.blacklist);

  createAsyncListIdReducer(
    builder,
    (s) => s.episodeList,
    "sonarrEpisodeId",
    episodeUpdateBy
  );

  createAsyncListIdReducer(
    builder,
    (s) => s.episodeList,
    "sonarrEpisodeId",
    episodeUpdateById,
    episodesRemoveItems
  );
});

export default reducer;
