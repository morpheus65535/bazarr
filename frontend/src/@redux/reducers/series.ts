import { createReducer } from "@reduxjs/toolkit";
import {
  episodesRemoveItems,
  episodeUpdateBy,
  episodeUpdateById,
  seriesRemoveItems,
  seriesRemoveWanted,
  seriesUpdateBlacklist,
  seriesUpdateHistoryList,
  seriesUpdateList,
  seriesUpdateWantedList,
} from "../actions";
import { defaultAOS } from "../utils";
import { AsyncUtility } from "../utils/async";
import {
  createAOSReducer,
  createAOSWholeReducer,
  createAsyncListIdReducer,
  createAsyncListReducer,
  removeOrderListItem,
} from "../utils/factory";

interface Series {
  seriesList: AsyncOrderState<Item.Series>;
  wantedEpisodesList: AsyncOrderState<Wanted.Episode>;
  episodeList: Async.List<Item.Episode>;
  historyList: Async.List<History.Episode>;
  blacklist: Async.List<Blacklist.Episode>;
}

const defaultSeries: Series = {
  seriesList: defaultAOS(),
  wantedEpisodesList: defaultAOS(),
  episodeList: AsyncUtility.getDefaultList(),
  historyList: AsyncUtility.getDefaultList(),
  blacklist: AsyncUtility.getDefaultList(),
};

const reducer = createReducer(defaultSeries, (builder) => {
  createAOSWholeReducer(
    builder,
    seriesUpdateList,
    (s) => s.seriesList,
    "sonarrSeriesId"
  );

  createAOSReducer(
    builder,
    seriesUpdateWantedList,
    (s) => s.wantedEpisodesList,
    "sonarrEpisodeId"
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
    "sonarrSeriesId",
    episodeUpdateBy
  );

  createAsyncListIdReducer(
    builder,
    (s) => s.episodeList,
    "sonarrEpisodeId",
    episodeUpdateById,
    episodesRemoveItems
  );

  builder.addCase(seriesRemoveWanted, (state, action) => {
    removeOrderListItem(state.wantedEpisodesList, action);
  });

  builder.addCase(seriesRemoveItems, (state, action) => {
    removeOrderListItem(state.seriesList, action);
  });
});

export default reducer;
