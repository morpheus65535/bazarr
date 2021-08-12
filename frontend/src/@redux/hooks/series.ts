import { useCallback, useMemo } from "react";
import { useEntityItemById, useEntityToList } from "../../utilites";
import {
  episodesUpdateBlacklist,
  episodesUpdateHistory,
  episodeUpdateById,
  episodeUpdateBySeriesId,
  seriesUpdateById,
} from "../actions";
import { useAutoListUpdate, useAutoUpdate } from "./async";
import { useReduxAction, useReduxStore } from "./base";

export function useSerieEntities() {
  const items = useReduxStore((d) => d.series.seriesList);
  return items;
}

export function useSeries() {
  const rawSeries = useSerieEntities();
  const content = useEntityToList(rawSeries.content);
  const series = useMemo<Async.List<Item.Series>>(() => {
    return {
      ...rawSeries,
      keyName: rawSeries.content.keyName,
      content,
    };
  }, [rawSeries, content]);
  return series;
}

export function useSerieBy(id: number) {
  const series = useSerieEntities();
  const action = useReduxAction(seriesUpdateById);
  const serie = useEntityItemById(series, id.toString());

  const update = useCallback(() => {
    if (!isNaN(id)) {
      action([id]);
    }
  }, [id, action]);

  useAutoUpdate(serie, update);
  return serie;
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

  const updateIds = useReduxAction(episodeUpdateById);

  useAutoListUpdate(state, update, updateIds);
  return state;
}

export function useWantedSeries() {
  const items = useReduxStore((d) => d.series.wantedEpisodesList);

  return items;
}

export function useBlacklistSeries() {
  const update = useReduxAction(episodesUpdateBlacklist);
  const items = useReduxStore((d) => d.series.blacklist);

  useAutoUpdate(items, update);
  return items;
}

export function useSeriesHistory() {
  const update = useReduxAction(episodesUpdateHistory);
  const items = useReduxStore((s) => s.series.historyList);

  useAutoUpdate(items, update);
  return items;
}
