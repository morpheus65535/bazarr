import { useCallback, useMemo } from "react";
import { buildOrderList } from "../../utilites";
import {
  episodeUpdateBySeriesId,
  movieUpdateBlacklist,
  movieUpdateHistoryList,
  movieUpdateInfoAll,
  providerUpdateAll,
  seriesUpdateBlacklist,
  seriesUpdateHistoryList,
  seriesUpdateInfoAll,
  seriesUpdateWantedAll,
  systemUpdateLanguages,
  systemUpdateLanguagesProfiles,
  systemUpdateSettingsAll,
} from "../actions";
import { useReduxAction, useReduxStore } from "./base";

function stateBuilder<T, D extends (...args: any[]) => any>(
  t: T,
  d: D
): [Readonly<T>, D] {
  return [t, d];
}

export function useSystemSettings() {
  const action = useReduxAction(systemUpdateSettingsAll);
  const items = useReduxStore((s) => s.system.settings);
  return stateBuilder(items, action);
}

export function useLanguageProfiles() {
  const action = useReduxAction(systemUpdateLanguagesProfiles);
  const items = useReduxStore((s) => s.system.languagesProfiles.data);

  return stateBuilder(items, action);
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
  const items = useReduxStore((s) =>
    enabled ? s.system.enabledLanguage.data : s.system.languages.data
  );
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
export function useProfileItems(profile?: Profile.Languages) {
  const getter = useLanguageGetter(true);

  return useMemo(
    () =>
      profile?.items.map<Language>(({ language, hi, forced }) => {
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
  const action = useReduxAction(seriesUpdateInfoAll);
  const items = useReduxStore((d) => d.series.seriesList);
  return stateBuilder(items, action);
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
  const [series, updateSeries] = useSeries();
  const item = useMemo<AsyncState<Item.Series | null>>(
    () => ({
      ...series,
      data: series.data.find((v) => v?.sonarrSeriesId === id) ?? null,
    }),
    [id, series]
  );
  const update = useCallback(() => {
    if (id) {
      updateSeries(id);
    }
  }, [id, updateSeries]);

  return stateBuilder(item, update);
}

export function useEpisodesBy(seriesId?: number) {
  const action = useReduxAction(episodeUpdateBySeriesId);
  const callback = useCallback(() => {
    if (seriesId !== undefined) {
      action(seriesId);
    }
  }, [action, seriesId]);

  const list = useReduxStore((d) => d.series.episodeList);

  const items = useMemo(() => {
    if (seriesId !== undefined) {
      return list.data[seriesId] ?? [];
    } else {
      return [];
    }
  }, [seriesId, list.data]);

  const state: AsyncState<Item.Episode[]> = {
    ...list,
    data: items,
  };

  return stateBuilder(state, callback);
}

export function useRawMovies() {
  const action = useReduxAction(movieUpdateInfoAll);
  const items = useReduxStore((d) => d.movie.movieList);
  return stateBuilder(items, action);
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
  const [movies, updateMovies] = useMovies();
  const item = useMemo<AsyncState<Item.Movie | null>>(
    () => ({
      ...movies,
      data: movies.data.find((v) => v?.radarrId === id) ?? null,
    }),
    [id, movies]
  );
  const update = useCallback(() => {
    if (id) {
      updateMovies(id);
    }
  }, [id, updateMovies]);

  return stateBuilder(item, update);
}

export function useWantedSeries() {
  const action = useReduxAction(seriesUpdateWantedAll);
  const items = useReduxStore((d) => d.series.wantedSeriesList);

  return stateBuilder(items, action);
}

export function useWantedMovies() {
  const [movies, action] = useMovies();

  const items = useMemo<AsyncState<Item.Movie[]>>(() => {
    const items = movies.data.filter(
      (v) => v !== null && v.missing_subtitles.length !== 0
    ) as Item.Movie[];
    return {
      ...movies,
      data: items,
    };
  }, [movies]);

  return stateBuilder(items, action);
}

export function useProviders() {
  const action = useReduxAction(providerUpdateAll);
  const items = useReduxStore((d) => d.system.providers);

  return stateBuilder(items, action);
}

export function useBlacklistMovies() {
  const action = useReduxAction(movieUpdateBlacklist);
  const items = useReduxStore((d) => d.movie.blacklist);

  return stateBuilder(items, action);
}

export function useBlacklistSeries() {
  const action = useReduxAction(seriesUpdateBlacklist);
  const items = useReduxStore((d) => d.series.blacklist);

  return stateBuilder(items, action);
}

export function useMoviesHistory() {
  const action = useReduxAction(movieUpdateHistoryList);
  const items = useReduxStore((s) => s.movie.historyList);

  return stateBuilder(items, action);
}

export function useSeriesHistory() {
  const action = useReduxAction(seriesUpdateHistoryList);
  const items = useReduxStore((s) => s.series.historyList);

  return stateBuilder(items, action);
}
