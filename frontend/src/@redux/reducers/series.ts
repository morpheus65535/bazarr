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
import { defaultAOS, defaultAS } from "../utils";
import {
  createAOSReducer,
  createAOSWholeReducer,
  createAsyncListReducer,
  createAsyncStateReducer,
  removeAsyncListItem,
  removeOrderListItem,
} from "../utils/factory";

interface Series {
  seriesList: AsyncOrderState<Item.Series>;
  wantedEpisodesList: AsyncOrderState<Wanted.Episode>;
  episodeList: AsyncState<Item.Episode[]>;
  historyList: AsyncState<Array<History.Episode>>;
  blacklist: AsyncState<Array<Blacklist.Episode>>;
}

const defaultSeries: Series = {
  seriesList: defaultAOS(),
  wantedEpisodesList: defaultAOS(),
  episodeList: defaultAS([]),
  historyList: defaultAS([]),
  blacklist: defaultAS([]),
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

  createAsyncStateReducer(
    builder,
    seriesUpdateHistoryList,
    (s) => s.historyList
  );

  createAsyncStateReducer(builder, seriesUpdateBlacklist, (s) => s.blacklist);

  createAsyncListReducer(
    builder,
    episodeUpdateBy,
    (s) => s.episodeList,
    "sonarrSeriesId"
  );

  createAsyncListReducer(
    builder,
    episodeUpdateById,
    (s) => s.episodeList,
    "sonarrEpisodeId"
  );

  builder.addCase(seriesRemoveWanted, (state, action) => {
    removeOrderListItem(state.wantedEpisodesList, action);
  });

  builder.addCase(seriesRemoveItems, (state, action) => {
    removeOrderListItem(state.seriesList, action);
  });

  builder.addCase(episodesRemoveItems, (state, action) => {
    removeAsyncListItem(state.episodeList, action, "sonarrEpisodeId");
  });
});

export default reducer;
