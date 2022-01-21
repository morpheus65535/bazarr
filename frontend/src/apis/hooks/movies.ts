import { useQuery } from "react-query";
import { createMovieId } from "../../utilities";
import QueryKeys from "../queries/keys";
import api from "../raw";

export function useMoviesByIds(ids: number[]) {
  const keys = ids.map(createMovieId);
  return useQuery([QueryKeys.movies, ...keys], () => api.movies.movies(ids));
}

export function useMovies() {
  return useQuery(QueryKeys.movies, () => api.movies.movies());
}

export function useMovieBlacklist() {
  return useQuery([QueryKeys.movies, QueryKeys.blacklist], () =>
    api.movies.blacklist()
  );
}
