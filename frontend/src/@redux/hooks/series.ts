import { useCallback, useEffect, useMemo } from "react";
import { useEntityItemById, useEntityToList } from "../../utilites";
import {
  episodesUpdateBlacklist,
  episodesUpdateHistory,
  episodeUpdateById,
  episodeUpdateBySeriesId,
  seriesUpdateById,
  seriesUpdateWantedById,
} from "../actions";
import { useAutoDirtyUpdate, useAutoUpdate } from "./async";
import { useReduxAction, useReduxStore } from "./base";

export function useSerieEntities() {
  const items = useReduxStore((d) => d.series.seriesList);

  useAutoDirtyUpdate(items, seriesUpdateById);
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
  const serie = useEntityItemById(series, String(id));

  const update = useCallback(() => {
    console.log("try loading", id);
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

  const newList: Async.List<Item.Episode> = useMemo(
    () => ({
      ...episodes,
      content: newContent,
    }),
    [episodes, newContent]
  );

  // FIXME
  useEffect(() => {
    update();
  }, [update]);

  useAutoDirtyUpdate(episodes, episodeUpdateById);

  return newList;
}

export function useWantedSeries() {
  const items = useReduxStore((d) => d.series.wantedEpisodesList);

  useAutoDirtyUpdate(items, seriesUpdateWantedById);
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
