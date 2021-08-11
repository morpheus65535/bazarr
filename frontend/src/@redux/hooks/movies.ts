import { useCallback, useEffect, useMemo } from "react";
import { useSocketIOReducer } from "../../@socketio/hooks";
import { useEntityAsList } from "../../utilites";
import {
  movieUpdateBlacklist,
  movieUpdateById,
  movieUpdateHistory,
  movieUpdateWantedById,
} from "../actions";
import { useAutoUpdateItem } from "./async";
import { stateBuilder, useReduxAction, useReduxStore } from "./base";

export function useMovieEntities() {
  const update = useReduxAction(movieUpdateById);
  const items = useReduxStore((d) => d.movies.movieList);
  return stateBuilder(items, update);
}

export function useMovies() {
  const [rawMovies, action] = useMovieEntities();
  const content = useEntityAsList(rawMovies.content);
  const movies = useMemo<Async.List<Item.Movie>>(() => {
    return {
      ...rawMovies,
      content,
    };
  }, [rawMovies, content]);
  return stateBuilder(movies, action);
}

export function useMovieBy(id?: number) {
  const [movies, updateMovies] = useMovieEntities();
  const movie = useMemo<Async.Item<Item.Movie>>(() => {
    const {
      content: { entities },
    } = movies;
    let content: Item.Movie | null = null;
    if (id && !isNaN(id) && id.toString() in entities) {
      content = entities[id.toString()];
    }
    return {
      ...movies,
      content,
    };
  }, [id, movies]);

  const update = useCallback(() => {
    if (id && !isNaN(id)) {
      updateMovies([id]);
    }
  }, [id, updateMovies]);

  useEffect(() => {
    if (movie.content === null && movie.state !== "loading") {
      update();
    }
  }, [movie, update]);
  return stateBuilder(movie, update);
}

export function useWantedMovies() {
  const update = useReduxAction(movieUpdateWantedById);
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

  useAutoUpdateItem(items, update);
  return stateBuilder(items, update);
}

export function useMoviesHistory() {
  const update = useReduxAction(movieUpdateHistory);
  const items = useReduxStore((s) => s.movies.historyList);
  const reducer = useMemo<SocketIO.Reducer>(
    () => ({ key: "movie-history", update }),
    [update]
  );
  useSocketIOReducer(reducer);

  useAutoUpdateItem(items, update);
  return stateBuilder(items, update);
}
