import { useCallback, useEffect, useMemo } from "react";
import { useEntityItemById, useEntityToList } from "../../utilites";
import {
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
      keyName: rawSeries.content.keyName,
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

export function useEpisodesBy(seriesId: number) {
  const action = useReduxAction(episodeUpdateBySeriesId);
  const update = useCallback(() => {
    if (!isNaN(seriesId)) {
      action([seriesId]);
    }
  }, [action, seriesId]);

  const episodes = useReduxStore((d) => d.series.episodeList);

  const newContent = useMemo(() => {
    return episodes.content.filter((v) => v.sonarrSeriesId === seriesId);
  }, [seriesId, episodes.content]);

  const state: Async.List<Item.Episode> = useMemo(
    () => ({
      ...episodes,
      content: newContent,
    }),
    [episodes, newContent]
  );

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

  useAutoUpdate(items, update);
  return stateBuilder(items, update);
}

export function useSeriesHistory() {
  const update = useReduxAction(seriesUpdateHistory);
  const items = useReduxStore((s) => s.series.historyList);

  useAutoUpdate(items, update);
  return stateBuilder(items, update);
}
