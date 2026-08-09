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

export const useMovieById = (id: number) => {
  return useQuery({
    queryKey: [QueryKeys.Movies, id],

    queryFn: async () => {
      const response = await api.movies.movies([id]);
      return response.length > 0 ? response[0] : undefined;
    },
  });
};

export const useMovies = (state: Parameter.ListState = {}) => {
  const client = useQueryClient();

  const query = useQuery({
    queryKey: [QueryKeys.Movies, QueryKeys.All, state],
    queryFn: async () => {
      const response = await api.movies.moviesBy({
        start: 0,
        length: -1,
        ...state,
      });
      return response.data;
    },
  });

  useEffect(() => {
    if (query.isSuccess && query.data) {
      cacheMovies(client, query.data);
    }
  }, [query.isSuccess, query.data, client]);

  return query;
};

export const useMovieTags = () =>
  useQuery({
    queryKey: [QueryKeys.Movies, QueryKeys.Tags],
    queryFn: () => api.movies.tags(),
    staleTime: Infinity,
  });

export const moviesPaginationKey = [QueryKeys.Movies];

export const moviesPaginationQuery: RangeQuery<Item.Movie> = (param) =>
  api.movies.moviesBy(param);

export const useMovieModification = () => {
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
};

export const useMovieAction = () => {
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
};

export const useMovieWantedPagination = () => {
  return usePaginationQuery([QueryKeys.Movies, QueryKeys.Wanted], (param) =>
    api.movies.wanted(param),
  );
};

export const useMovieBlacklist = () => {
  return useQuery({
    queryKey: [QueryKeys.Movies, QueryKeys.Blacklist],

    queryFn: () => api.movies.blacklist(),
  });
};

export const useMovieAddBlacklist = () => {
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
};

export const useMovieDeleteBlacklist = () => {
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
};

export const useMovieHistoryPagination = () => {
  return usePaginationQuery(
    [QueryKeys.Movies, QueryKeys.History],
    (param) => api.movies.history(param),
    false,
  );
};

export const useMovieHistory = (radarrId?: number) => {
  return useQuery({
    queryKey: [QueryKeys.Movies, QueryKeys.History, radarrId],

    queryFn: () => {
      if (radarrId) {
        return api.movies.historyBy(radarrId);
      }

      return [];
    },
  });
};
