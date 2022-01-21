import { useMutation, useQuery, useQueryClient } from "react-query";
import { createMovieId } from "src/utilities";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useMoviesByIds(ids: number[]) {
  return useQuery([QueryKeys.Movies, ids], () => api.movies.movies(ids));
}

export function useMovie(id: number) {
  return useQuery([QueryKeys.Movies, id], () => api.movies.movies([id]));
}

export function useMovies() {
  return useQuery([QueryKeys.Movies], () => api.movies.movies());
}

export function useMovieModification() {
  const client = useQueryClient();
  return useMutation((form: FormType.ModifyItem) => api.movies.modify(form), {
    onSuccess: (_, form) => {
      form.id.forEach((id) => client.invalidateQueries(createMovieId(id)));
    },
  });
}

export function useMovieBlacklist() {
  return useQuery([QueryKeys.Movies, QueryKeys.Blacklist], () =>
    api.movies.blacklist()
  );
}
