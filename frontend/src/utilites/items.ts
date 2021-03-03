import { useEffect, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import { providerUpdateAll } from "../@redux/actions";

export function useWantedMovies(): AsyncState<Item.Movie[]> {
  const movies = useSelector<ReduxStore, AsyncState<Item.Movie[]>>(
    (d) => d.movie.movieList
  );
  return useMemo(() => {
    movies.items = movies.items.filter((v) => v.missing_subtitles.length !== 0);
    return movies;
  }, [movies]);
}

export function useProviders(): AsyncState<SystemProvider[]> {
  const dispatch = useDispatch();
  useEffect(() => {
    // Trigger update when we use it
    dispatch(providerUpdateAll());
  }, [dispatch]);
  return useSelector<ReduxStore, AsyncState<SystemProvider[]>>(
    (d) => d.system.providers
  );
}
