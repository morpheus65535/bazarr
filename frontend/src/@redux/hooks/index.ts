import { useCallback, useEffect, useMemo } from "react";
import { useSocketIOReducer, useWrapToOptionalId } from "../../@socketio/hooks";
import { buildOrderList } from "../../utilites";
import {
  episodesRemoveItems,
  episodeUpdateBy,
  episodeUpdateById,
  movieUpdateBlacklist,
  movieUpdateHistoryList,
  movieUpdateList,
  movieUpdateWantedList,
  providerUpdateList,
  seriesUpdateBlacklist,
  seriesUpdateHistoryList,
  seriesUpdateList,
  seriesUpdateWantedList,
  systemUpdateAllSettings,
  systemUpdateHealth,
  systemUpdateLanguages,
  systemUpdateLanguagesProfiles,
  systemUpdateLogs,
  systemUpdateReleases,
  systemUpdateStatus,
  systemUpdateTasks,
} from "../actions";
import { useReduxAction, useReduxStore } from "./base";

function stateBuilder<T, D extends (...args: any[]) => any>(
  t: T,
  d: D
): [Readonly<T>, D] {
  return [t, d];
}

export function useSystemSettings() {
  const update = useReduxAction(systemUpdateAllSettings);
  const items = useReduxStore((s) => s.system.settings);

  return stateBuilder(items, update);
}

export function useSystemLogs() {
  const items = useReduxStore(({ system }) => system.logs);
  const update = useReduxAction(systemUpdateLogs);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(items, update);
}

export function useSystemTasks() {
  const items = useReduxStore((s) => s.system.tasks);
  const update = useReduxAction(systemUpdateTasks);
  const reducer = useMemo<SocketIO.Reducer>(() => ({ key: "task", update }), [
    update,
  ]);
  useSocketIOReducer(reducer);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(items, update);
}

export function useSystemStatus() {
  const { content } = useReduxStore((s) => s.system.status);
  const update = useReduxAction(systemUpdateStatus);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(content, update);
}

export function useSystemHealth() {
  const update = useReduxAction(systemUpdateHealth);
  const items = useReduxStore((s) => s.system.health);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(items, update);
}

export function useSystemProviders() {
  const update = useReduxAction(providerUpdateList);
  const items = useReduxStore((d) => d.system.providers);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(items, update);
}

export function useSystemReleases() {
  const items = useReduxStore(({ system }) => system.releases);
  const update = useReduxAction(systemUpdateReleases);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(items, update);
}

export function useLanguageProfiles() {
  const action = useReduxAction(systemUpdateLanguagesProfiles);
  const { content } = useReduxStore((s) => s.system.languagesProfiles);

  return stateBuilder(content, action);
}

export function useProfileBy(id: number | null | undefined) {
  const [profiles] = useLanguageProfiles();
  return useMemo(() => profiles.find((v) => v.profileId === id), [
    id,
    profiles,
  ]);
}

export function useLanguages(enabled: boolean = false) {
  const action = useReduxAction(systemUpdateLanguages);
  const data = useReduxStore((s) => s.system.languages);

  const items = useMemo(() => {
    return data.content.flatMap<Language.Info>((curr) => {
      if (!enabled || curr.enabled) {
        return [{ code2: curr.code2, name: curr.name }];
      } else {
        return [];
      }
    });
  }, [data, enabled]);

  return stateBuilder(items, action);
}

function useLanguageGetter(enabled: boolean = false) {
  const [languages] = useLanguages(enabled);
  return useCallback(
    (code?: string) => {
      if (code === undefined) {
        return undefined;
      } else {
        return languages.find((v) => v.code2 === code);
      }
    },
    [languages]
  );
}

export function useLanguageBy(code?: string) {
  const getter = useLanguageGetter();
  return useMemo(() => getter(code), [code, getter]);
}

// Convert languageprofile items to language
export function useProfileItems(profile?: Language.Profile) {
  const getter = useLanguageGetter(true);

  return useMemo(
    () =>
      profile?.items.map<Language.Info>(({ language, hi, forced }) => {
        const name = getter(language)?.name ?? "";
        return {
          hi: hi === "True",
          forced: forced === "True",
          code2: language,
          name,
        };
      }) ?? [],
    [getter, profile?.items]
  );
}

export function useRawSeries() {
  const update = useReduxAction(seriesUpdateList);
  const items = useReduxStore((d) => d.series.seriesList);
  return stateBuilder(items, update);
}

export function useSeries(order = true) {
  const [rawSeries, action] = useRawSeries();
  const series = useMemo<AsyncState<Item.Series[]>>(() => {
    const state = rawSeries.data;
    if (order) {
      return {
        ...rawSeries,
        data: buildOrderList(state),
      };
    } else {
      return {
        ...rawSeries,
        data: Object.values(state.items),
      };
    }
  }, [rawSeries, order]);
  return stateBuilder(series, action);
}

export function useSerieBy(id?: number) {
  const [series, updateSerie] = useRawSeries();
  const serie = useMemo<AsyncState<Item.Series | null>>(() => {
    const items = series.data.items;
    let item: Item.Series | null = null;
    if (id && !isNaN(id) && id in items) {
      item = items[id];
    }
    return {
      ...series,
      data: item,
    };
  }, [id, series]);

  const update = useCallback(() => {
    if (id && !isNaN(id)) {
      updateSerie([id]);
    }
  }, [id, updateSerie]);

  useEffect(() => {
    if (serie.data === null) {
      update();
    }
  }, [serie.data, update]);
  return stateBuilder(serie, update);
}

export function useEpisodesBy(seriesId?: number) {
  const action = useReduxAction(episodeUpdateBy);
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

  const state: Async.BaseType<Item.Episode[]> = useMemo(
    () => ({
      ...list,
      content: items,
    }),
    [list, items]
  );

  const updateById = useReduxAction(episodeUpdateById);
  const wrappedUpdateById = useWrapToOptionalId(updateById);
  const deleteAction = useReduxAction(episodesRemoveItems);
  const wrappedDelete = useWrapToOptionalId(deleteAction);

  const episodeReducer = useMemo<SocketIO.Reducer>(
    () => ({
      key: "episode",
      update: wrappedUpdateById,
      delete: wrappedDelete,
    }),
    [wrappedUpdateById, wrappedDelete]
  );
  useSocketIOReducer(episodeReducer);

  const wrapAction = useWrapToOptionalId(action);
  const seriesReducer = useMemo<SocketIO.Reducer>(
    () => ({ key: "series", update: wrapAction }),
    [wrapAction]
  );
  useSocketIOReducer(seriesReducer);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(state, update);
}

export function useRawMovies() {
  const update = useReduxAction(movieUpdateList);
  const items = useReduxStore((d) => d.movies.movieList);
  return stateBuilder(items, update);
}

export function useMovies(order = true) {
  const [rawMovies, action] = useRawMovies();
  const movies = useMemo<AsyncState<Item.Movie[]>>(() => {
    const state = rawMovies.data;
    if (order) {
      return {
        ...rawMovies,
        data: buildOrderList(state),
      };
    } else {
      return {
        ...rawMovies,
        data: Object.values(state.items),
      };
    }
  }, [rawMovies, order]);
  return stateBuilder(movies, action);
}

export function useMovieBy(id?: number) {
  const [movies, updateMovies] = useRawMovies();
  const movie = useMemo<AsyncState<Item.Movie | null>>(() => {
    const items = movies.data.items;
    let item: Item.Movie | null = null;
    if (id && !isNaN(id) && id in items) {
      item = items[id];
    }
    return {
      ...movies,
      data: item,
    };
  }, [id, movies]);

  const update = useCallback(() => {
    if (id && !isNaN(id)) {
      updateMovies([id]);
    }
  }, [id, updateMovies]);

  useEffect(() => {
    if (movie.data === null) {
      update();
    }
  }, [movie.data, update]);
  return stateBuilder(movie, update);
}

export function useWantedSeries() {
  const update = useReduxAction(seriesUpdateWantedList);
  const items = useReduxStore((d) => d.series.wantedEpisodesList);

  return stateBuilder(items, update);
}

export function useWantedMovies() {
  const update = useReduxAction(movieUpdateWantedList);
  const items = useReduxStore((d) => d.movies.wantedMovieList);

  return stateBuilder(items, update);
}

export function useBlacklistMovies() {
  const update = useReduxAction(movieUpdateBlacklist);
  const items = useReduxStore((d) => d.movies.blacklist);
  const reducer = useMemo<SocketIO.Reducer>(
    () => ({ key: "movie-blacklist", any: update }),
    [update]
  );
  useSocketIOReducer(reducer);

  useEffect(() => {
    update();
  }, [update]);
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

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(items, update);
}

export function useMoviesHistory() {
  const update = useReduxAction(movieUpdateHistoryList);
  const items = useReduxStore((s) => s.movies.historyList);
  const reducer = useMemo<SocketIO.Reducer>(
    () => ({ key: "movie-history", update }),
    [update]
  );
  useSocketIOReducer(reducer);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(items, update);
}

export function useSeriesHistory() {
  const update = useReduxAction(seriesUpdateHistoryList);
  const items = useReduxStore((s) => s.series.historyList);
  const reducer = useMemo<SocketIO.Reducer>(
    () => ({ key: "episode-history", update }),
    [update]
  );
  useSocketIOReducer(reducer);

  useEffect(() => {
    update();
  }, [update]);
  return stateBuilder(items, update);
}
