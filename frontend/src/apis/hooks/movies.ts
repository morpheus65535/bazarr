import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "react-query";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

const cacheMovies = (client: QueryClient, movies: Item.Movie[]) => {
  movies.forEach((item) => {
    client.setQueryData([QueryKeys.Movies, item.radarrId], item);
  });
};

export function useMoviesByIds(ids: number[]) {
  const client = useQueryClient();
  return useQuery([QueryKeys.Movies, ...ids], () => api.movies.movies(ids), {
    onSuccess: (data) => {
      cacheMovies(client, data);
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
  return useQuery(
    [QueryKeys.Movies, QueryKeys.All],
    () => api.movies.movies(),
    {
      onSuccess: (data) => {
        cacheMovies(client, data);
      },
    }
  );
}

export function useMovieModification() {
  const client = useQueryClient();
  return useMutation((form: FormType.ModifyItem) => api.movies.modify(form), {
    onSuccess: (_, form) => {
      form.id.forEach((v) => {
        client.invalidateQueries([QueryKeys.Movies, v]);
      });
      client.invalidateQueries([QueryKeys.Movies, QueryKeys.Range]);
      client.invalidateQueries([QueryKeys.Movies, QueryKeys.History]);
      client.invalidateQueries([QueryKeys.Movies, QueryKeys.Wanted]);
    },
  });
}

export function useMovieBlacklist() {
  return useQuery([QueryKeys.Movies, QueryKeys.Blacklist], () =>
    api.movies.blacklist()
  );
}
