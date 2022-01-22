import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "react-query";
import { usePaginationQuery } from "../queries/hooks";
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

export function useMoviesPagination() {
  return usePaginationQuery([QueryKeys.Movies], (param) =>
    api.movies.moviesBy(param)
  );
}

export function useMovieModification() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.Movies],
    (form: FormType.ModifyItem) => api.movies.modify(form),
    {
      onSuccess: (_, form) => {
        form.id.forEach((v) => {
          client.invalidateQueries([QueryKeys.Movies, v]);
        });
        client.invalidateQueries([QueryKeys.Movies, QueryKeys.Range]);
        client.invalidateQueries([QueryKeys.Movies, QueryKeys.History]);
        client.invalidateQueries([QueryKeys.Movies, QueryKeys.Wanted]);
      },
    }
  );
}

export function useMovieAction() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.Actions, QueryKeys.Movies],
    (form: FormType.MoviesAction) => api.movies.action(form),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.Movies]);
      },
    }
  );
}

export function useMovieWantedPagination() {
  return usePaginationQuery([QueryKeys.Movies, QueryKeys.Wanted], (param) =>
    api.movies.wanted(param)
  );
}

export function useMovieBlacklist() {
  return useQuery([QueryKeys.Movies, QueryKeys.Blacklist], () =>
    api.movies.blacklist()
  );
}

export function useMovieAddBlacklist() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.Movies, QueryKeys.Blacklist],
    (param: { id: number; form: FormType.AddBlacklist }) => {
      const { id, form } = param;
      return api.movies.addBlacklist(id, form);
    },
    {
      onSuccess: (_, { id }) => {
        client.invalidateQueries([QueryKeys.Movies, QueryKeys.Blacklist]);
        client.invalidateQueries([QueryKeys.Movies, id]);
      },
    }
  );
}

export function useMovieDeleteBlacklist() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.Movies, QueryKeys.Blacklist],
    (param: { all?: boolean; form?: FormType.DeleteBlacklist }) =>
      api.movies.deleteBlacklist(param.all, param.form),
    {
      onSuccess: (_, param) => {
        client.invalidateQueries([QueryKeys.Movies, QueryKeys.Blacklist]);
      },
    }
  );
}

export function useMovieHistoryPagination() {
  return usePaginationQuery([QueryKeys.Movies, QueryKeys.History], (param) =>
    api.movies.history(param)
  );
}

export function useMovieHistory(radarrId?: number) {
  return useQuery([QueryKeys.Movies, QueryKeys.History, radarrId], () => {
    if (radarrId) {
      return api.movies.historyBy(radarrId);
    }
  });
}
