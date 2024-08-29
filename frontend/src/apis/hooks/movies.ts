import { useEffect } from "react";
import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { usePaginationQuery } from "@/apis/queries/hooks";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

const cacheMovies = (client: QueryClient, movies: Item.Movie[]) => {
  movies.forEach((item) => {
    client.setQueryData([QueryKeys.Movies, item.radarrId], item);
  });
};

export function useMovieById(id: number) {
  return useQuery({
    queryKey: [QueryKeys.Movies, id],

    queryFn: async () => {
      const response = await api.movies.movies([id]);
      return response.length > 0 ? response[0] : undefined;
    },
  });
}

export function useMovies() {
  const client = useQueryClient();

  const query = useQuery({
    queryKey: [QueryKeys.Movies, QueryKeys.All],
    queryFn: () => api.movies.movies(),
  });

  useEffect(() => {
    if (query.isSuccess && query.data) {
      cacheMovies(client, query.data);
    }
  }, [query.isSuccess, query.data, client]);

  return query;
}

export function useMoviesPagination() {
  return usePaginationQuery([QueryKeys.Movies], (param) =>
    api.movies.moviesBy(param),
  );
}

export function useMovieModification() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.Movies],
    mutationFn: (form: FormType.ModifyItem) => api.movies.modify(form),

    onSuccess: (_, form) => {
      form.id.forEach((v) => {
        void client.invalidateQueries({
          queryKey: [QueryKeys.Movies, v],
        });
      });

      // TODO: query less
      void client.invalidateQueries({
        queryKey: [QueryKeys.Movies],
      });
    },
  });
}

export function useMovieAction() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.Actions, QueryKeys.Movies],
    mutationFn: (form: FormType.MoviesAction) => api.movies.action(form),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.Movies],
      });
    },
  });
}

export function useMovieWantedPagination() {
  return usePaginationQuery([QueryKeys.Movies, QueryKeys.Wanted], (param) =>
    api.movies.wanted(param),
  );
}

export function useMovieBlacklist() {
  return useQuery({
    queryKey: [QueryKeys.Movies, QueryKeys.Blacklist],

    queryFn: () => api.movies.blacklist(),
  });
}

export function useMovieAddBlacklist() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.Movies, QueryKeys.Blacklist],

    mutationFn: (param: { id: number; form: FormType.AddBlacklist }) => {
      const { id, form } = param;
      return api.movies.addBlacklist(id, form);
    },

    onSuccess: (_, { id }) => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.Movies, QueryKeys.Blacklist],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.Movies, id],
      });
    },
  });
}

export function useMovieDeleteBlacklist() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.Movies, QueryKeys.Blacklist],

    mutationFn: (param: { all?: boolean; form?: FormType.DeleteBlacklist }) =>
      api.movies.deleteBlacklist(param.all, param.form),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.Movies, QueryKeys.Blacklist],
      });
    },
  });
}

export function useMovieHistoryPagination() {
  return usePaginationQuery(
    [QueryKeys.Movies, QueryKeys.History],
    (param) => api.movies.history(param),
    false,
  );
}

export function useMovieHistory(radarrId?: number) {
  return useQuery({
    queryKey: [QueryKeys.Movies, QueryKeys.History, radarrId],

    queryFn: () => {
      if (radarrId) {
        return api.movies.historyBy(radarrId);
      }

      return [];
    },
  });
}
