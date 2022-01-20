import { useQuery } from "react-query";
import { MoviesApi } from "..";
import { createMovieId } from "../../utilities";

export function useMoviesByIds(ids: number[]) {
  const keys = ids.map(createMovieId);
  return useQuery(["movies", ...keys], () => MoviesApi.movies(ids));
}

export function useMovies() {
  return useQuery("movies", () => MoviesApi.movies());
}

export function useMovieBlacklist() {
  return useQuery(["movies", "blacklist"], () => MoviesApi.blacklist());
}
