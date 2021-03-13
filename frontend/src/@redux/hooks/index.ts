import { useCallback, useMemo } from "react";
import { isNonNullable } from "../../utilites";
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
  const items = useReduxStore((s) => s.system.languagesProfiles.items);

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
    enabled ? s.system.enabledLanguage.items : s.system.languages.items
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

export function useSeries() {
  const action = useReduxAction(seriesUpdateInfoAll);
  const items = useReduxStore((d) => d.series.seriesList);
  const series = useMemo<AsyncState<Item.Series[]>>(
    () => ({
      ...items,
      items: items.items.filter((v) => isNonNullable(v)) as Item.Series[],
    }),
    [items]
  );
  return stateBuilder(series, action);
}

export function useSerieBy(id?: number) {
  const [series, updateSeries] = useSeries();
  const item = useMemo<AsyncState<Item.Series | null>>(
    () => ({
      ...series,
      items: series.items.find((v) => v?.sonarrSeriesId === id) ?? null,
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
      return list.items[seriesId] ?? [];
    } else {
      return [];
    }
  }, [seriesId, list.items]);

  const state: AsyncState<Item.Episode[]> = {
    ...list,
    items,
  };

  return stateBuilder(state, callback);
}

export function useMovies() {
  const action = useReduxAction(movieUpdateInfoAll);

  const items = useReduxStore((d) => d.movie.movieList);
  const movies = useMemo<AsyncState<Item.Movie[]>>(
    () => ({
      ...items,
      items: items.items.filter((v) => isNonNullable(v)) as Item.Movie[],
    }),
    [items]
  );

  return stateBuilder(movies, action);
}

export function useMovieBy(id?: number) {
  const [movies, updateMovies] = useMovies();
  const item = useMemo<AsyncState<Item.Movie | null>>(
    () => ({
      ...movies,
      items: movies.items.find((v) => v?.radarrId === id) ?? null,
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
    const items = movies.items.filter(
      (v) => v !== null && v.missing_subtitles.length !== 0
    ) as Item.Movie[];
    return {
      ...movies,
      items,
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
