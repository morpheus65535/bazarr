import { useCallback, useMemo } from "react";
import { useEntityItemById, useEntityToList } from "../../utilites";
import {
  movieUpdateBlacklist,
  movieUpdateById,
  movieUpdateHistory,
} from "../actions";
import { useAutoUpdate } from "./async";
import { useReduxAction, useReduxStore } from "./base";

export function useMovieEntities() {
  return useReduxStore((d) => d.movies.movieList);
}

export function useMovies() {
  const rawMovies = useMovieEntities();
  const content = useEntityToList(rawMovies.content);
  const movies = useMemo<Async.List<Item.Movie>>(() => {
    return {
      ...rawMovies,
      keyName: rawMovies.content.keyName,
      content,
    };
  }, [rawMovies, content]);
  return movies;
}

export function useMovieBy(id: number) {
  const movies = useMovieEntities();
  const action = useReduxAction(movieUpdateById);

  const update = useCallback(() => {
    if (!isNaN(id)) {
      action([id]);
    }
  }, [id, action]);

  const movie = useEntityItemById(movies, id.toString());

  useAutoUpdate(movie, update);
  return movie;
}

export function useWantedMovies() {
  const items = useReduxStore((d) => d.movies.wantedMovieList);

  return items;
}

export function useBlacklistMovies() {
  const update = useReduxAction(movieUpdateBlacklist);
  const items = useReduxStore((d) => d.movies.blacklist);

  useAutoUpdate(items, update);
  return items;
}

export function useMoviesHistory() {
  const update = useReduxAction(movieUpdateHistory);
  const items = useReduxStore((s) => s.movies.historyList);

  useAutoUpdate(items, update);
  return items;
}
