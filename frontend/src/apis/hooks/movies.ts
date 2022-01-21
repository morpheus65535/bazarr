import { useQuery } from "react-query";
import QueryKeys from "../queries/keys";
import api from "../raw";

export function useMoviesByIds(ids: number[]) {
  return useQuery([QueryKeys.movies, ...ids], () => api.movies.movies(ids));
}

export function useMovies() {
  return useQuery(QueryKeys.movies, () => api.movies.movies());
}

export function useMovieBlacklist() {
  return useQuery([QueryKeys.movies, { type: "blacklist" }], () =>
    api.movies.blacklist()
  );
}
