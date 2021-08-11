import { useCallback, useMemo } from "react";
import { useSocketIOReducer } from "../../@socketio/hooks";
import { useEntityItemById, useEntityToList } from "../../utilites";
import {
  movieUpdateBlacklist,
  movieUpdateById,
  movieUpdateHistory,
  movieUpdateWantedById,
} from "../actions";
import { useAutoUpdate } from "./async";
import { stateBuilder, useReduxAction, useReduxStore } from "./base";

export function useMovieEntities() {
  return useReduxStore((d) => d.movies.movieList);
}

export function useMovies() {
  const rawMovies = useMovieEntities();
  const action = useReduxAction(movieUpdateById);
  const content = useEntityToList(rawMovies.content);
  const movies = useMemo<Async.List<Item.Movie>>(() => {
    return {
      ...rawMovies,
      content,
    };
  }, [rawMovies, content]);
  return stateBuilder(movies, action);
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

  useAutoUpdate(items, update);
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

  useAutoUpdate(items, update);
  return stateBuilder(items, update);
}
