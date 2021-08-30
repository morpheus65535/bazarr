import { useCallback, useMemo } from "react";
import { useEntityItemById, useEntityToList } from "../../utilities";
import {
  movieUpdateBlacklist,
  movieUpdateById,
  movieUpdateWantedById,
} from "../actions";
import { useAutoDirtyUpdate, useAutoUpdate } from "./async";
import { useReduxAction, useReduxStore } from "./base";

export function useMovieEntities() {
  const entities = useReduxStore((d) => d.movies.movieList);

  useAutoDirtyUpdate(entities, movieUpdateById);

  return entities;
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

  useAutoDirtyUpdate(items, movieUpdateWantedById);
  return items;
}

export function useBlacklistMovies() {
  const update = useReduxAction(movieUpdateBlacklist);
  const items = useReduxStore((d) => d.movies.blacklist);

  useAutoUpdate(items, update);
  return items;
}

export function useMoviesHistory() {
  const items = useReduxStore((s) => s.movies.historyList);

  return items;
}
