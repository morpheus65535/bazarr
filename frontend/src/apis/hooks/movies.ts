import { useQuery } from "react-query";
import { createMovieId } from "../../utilities";
import api from "../raw";

export function useMoviesByIds(ids: number[]) {
  const keys = ids.map(createMovieId);
  return useQuery(["movies", ...keys], () => api.movies.movies(ids));
}

export function useMovies() {
  return useQuery("movies", () => api.movies.movies());
}

export function useMovieBlacklist() {
  return useQuery(["movies", "blacklist"], () => api.movies.blacklist());
}
