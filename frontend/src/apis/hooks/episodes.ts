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

const cacheEpisodes = (client: QueryClient, episodes: Item.Episode[]) => {
  episodes.forEach((item) => {
    client.setQueryData([QueryKeys.Episodes, item.sonarrEpisodeId], item);

    client.setQueryData(
      [
        QueryKeys.Series,
        item.sonarrSeriesId,
        QueryKeys.Episodes,
        item.sonarrEpisodeId,
      ],
      item,
    );
  });
};

export function useEpisodesBySeriesId(id: number) {
  const client = useQueryClient();

  const query = useQuery({
    queryKey: [QueryKeys.Series, id, QueryKeys.Episodes, QueryKeys.All],
    queryFn: () => api.episodes.bySeriesId([id]),
  });

  useEffect(() => {
    if (query.isSuccess && query.data) {
      cacheEpisodes(client, query.data);
    }
  }, [query.isSuccess, query.data, client]);

  return query;
}

export function useEpisodeWantedPagination() {
  return usePaginationQuery([QueryKeys.Series, QueryKeys.Wanted], (param) =>
    api.episodes.wanted(param),
  );
}

export function useEpisodeBlacklist() {
  return useQuery({
    queryKey: [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.Blacklist],
    queryFn: () => api.episodes.blacklist(),
  });
}

export function useEpisodeAddBlacklist() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.Blacklist],

    mutationFn: (param: {
      seriesId: number;
      episodeId: number;
      form: FormType.AddBlacklist;
    }) => {
      const { seriesId, episodeId, form } = param;
      return api.episodes.addBlacklist(seriesId, episodeId, form);
    },

    onSuccess: (_, { seriesId }) => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.Blacklist],
      });

      void client.invalidateQueries({
        queryKey: [QueryKeys.Series, seriesId],
      });
    },
  });
}

export function useEpisodeDeleteBlacklist() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.Blacklist],

    mutationFn: (param: { all?: boolean; form?: FormType.DeleteBlacklist }) =>
      api.episodes.deleteBlacklist(param.all, param.form),

    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.Blacklist],
      });
    },
  });
}

export function useEpisodeHistoryPagination() {
  return usePaginationQuery(
    [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.History],
    (param) => api.episodes.history(param),
    false,
  );
}

export function useEpisodeHistory(episodeId?: number) {
  return useQuery({
    queryKey: [
      QueryKeys.Series,
      QueryKeys.Episodes,
      QueryKeys.History,
      episodeId,
    ],

    queryFn: () => {
      if (episodeId) {
        return api.episodes.historyBy(episodeId);
      }

      return [];
    },
  });
}
