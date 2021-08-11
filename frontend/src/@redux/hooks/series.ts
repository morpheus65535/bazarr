import { useCallback, useEffect, useMemo } from "react";
import { useSocketIOReducer } from "../../@socketio/hooks";
import { useEntityItemById, useEntityToList } from "../../utilites";
import {
  episodesRemoveById,
  episodeUpdateByEpisodeId,
  episodeUpdateBySeriesId,
  seriesUpdateBlacklist,
  seriesUpdateById,
  seriesUpdateHistory,
  seriesUpdateWantedById,
} from "../actions";
import { useAutoUpdate } from "./async";
import { stateBuilder, useReduxAction, useReduxStore } from "./base";

export function useSerieEntities() {
  const update = useReduxAction(seriesUpdateById);
  const items = useReduxStore((d) => d.series.seriesList);
  return stateBuilder(items, update);
}

export function useSeries() {
  const [rawSeries, action] = useSerieEntities();
  const content = useEntityToList(rawSeries.content);
  const series = useMemo<Async.List<Item.Series>>(() => {
    return {
      ...rawSeries,
      content,
    };
  }, [rawSeries, content]);
  return stateBuilder(series, action);
}

export function useSerieBy(id: number) {
  const [series, updateSerie] = useSerieEntities();
  const serie = useEntityItemById(series, id.toString());

  const update = useCallback(() => {
    if (!isNaN(id)) {
      updateSerie([id]);
    }
  }, [id, updateSerie]);

  useAutoUpdate(serie, update);
  return stateBuilder(serie, update);
}

export function useEpisodesBy(seriesId?: number) {
  const action = useReduxAction(episodeUpdateBySeriesId);
  const update = useCallback(() => {
    if (seriesId !== undefined && !isNaN(seriesId)) {
      action([seriesId]);
    }
  }, [action, seriesId]);

  const list = useReduxStore((d) => d.series.episodeList);

  const items = useMemo(() => {
    if (seriesId !== undefined && !isNaN(seriesId)) {
      return list.content.filter((v) => v.sonarrSeriesId === seriesId);
    } else {
      return [];
    }
  }, [seriesId, list.content]);

  const state: Async.List<Item.Episode> = useMemo(
    () => ({
      ...list,
      content: items,
    }),
    [list, items]
  );

  const updateById = useReduxAction(episodeUpdateByEpisodeId);
  const deleteAction = useReduxAction(episodesRemoveById);

  const episodeReducer = useMemo<SocketIO.Reducer>(
    () => ({
      key: "episode",
      update: updateById,
      delete: deleteAction,
    }),
    [updateById, deleteAction]
  );
  useSocketIOReducer(episodeReducer);

  const seriesReducer = useMemo<SocketIO.Reducer>(
    () => ({ key: "series", update: action }),
    [action]
  );
  useSocketIOReducer(seriesReducer);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(state, update);
}

export function useWantedSeries() {
  const update = useReduxAction(seriesUpdateWantedById);
  const items = useReduxStore((d) => d.series.wantedEpisodesList);

  return stateBuilder(items, update);
}

export function useBlacklistSeries() {
  const update = useReduxAction(seriesUpdateBlacklist);
  const items = useReduxStore((d) => d.series.blacklist);
  const reducer = useMemo<SocketIO.Reducer>(
    () => ({ key: "episode-blacklist", any: update }),
    [update]
  );
  useSocketIOReducer(reducer);

  useAutoUpdate(items, update);
  return stateBuilder(items, update);
}

export function useSeriesHistory() {
  const update = useReduxAction(seriesUpdateHistory);
  const items = useReduxStore((s) => s.series.historyList);
  const reducer = useMemo<SocketIO.Reducer>(
    () => ({ key: "episode-history", update }),
    [update]
  );
  useSocketIOReducer(reducer);

  useAutoUpdate(items, update);
  return stateBuilder(items, update);
}
