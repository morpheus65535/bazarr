import { useMemo } from "react";
import { useSelector } from "react-redux";

export function useWantedMovies(): AsyncState<Item.Movie[]> {
  const movies = useSelector<ReduxStore, AsyncState<Item.Movie[]>>(
    (d) => d.movie.movieList
  );
  return useMemo(() => {
    movies.items = movies.items.filter((v) => v.missing_subtitles.length !== 0);
    return movies;
  }, [movies]);
}
