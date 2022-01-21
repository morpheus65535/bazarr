import { useMutation, useQuery, useQueryClient } from "react-query";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useMoviesByIds(ids: number[]) {
  const client = useQueryClient();
  return useQuery([QueryKeys.Movies, ...ids], () => api.movies.movies(ids), {
    onSuccess: (data) => {
      data.forEach((v) => {
        client.setQueryData([QueryKeys.Movies, v.radarrId], data);
      });
    },
  });
}

export function useMovieById(id: number) {
  return useQuery([QueryKeys.Movies, id], async () => {
    const response = await api.movies.movies([id]);
    return response.length > 0 ? response[0] : undefined;
  });
}

export function useMovies() {
  const client = useQueryClient();
  return useQuery([QueryKeys.Movies], () => api.movies.movies(), {
    onSuccess: (data) => {
      data.forEach((v) => {
        client.setQueryData([QueryKeys.Movies, v.radarrId], data);
      });
    },
  });
}

export function useMovieModification() {
  const client = useQueryClient();
  return useMutation((form: FormType.ModifyItem) => api.movies.modify(form), {
    onSuccess: (_, form) => {
      form.id.forEach((v) => {
        client.invalidateQueries([QueryKeys.Movies, v]);
      });
    },
  });
}

export function useMovieBlacklist() {
  return useQuery([QueryKeys.Movies, QueryKeys.Blacklist], () =>
    api.movies.blacklist()
  );
}
