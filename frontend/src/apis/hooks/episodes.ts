import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "react-query";
import { usePaginationQuery } from "../queries/hooks";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

const cacheEpisodes = (client: QueryClient, episodes: Item.Episode[]) => {
  episodes.forEach((item) => {
    client.setQueryData(
      [
        QueryKeys.Series,
        item.sonarrSeriesId,
        QueryKeys.Episodes,
        item.sonarrEpisodeId,
      ],
      item
    );
  });
};

export function useEpisodeByIds(ids: number[]) {
  const client = useQueryClient();
  return useQuery(
    [QueryKeys.Series, QueryKeys.Episodes, ids],
    () => api.episodes.byEpisodeId(ids),
    {
      onSuccess: (data) => {
        cacheEpisodes(client, data);
      },
    }
  );
}

export function useEpisodeBySeriesId(id: number) {
  const client = useQueryClient();
  return useQuery(
    [QueryKeys.Series, id, QueryKeys.Episodes, QueryKeys.All],
    () => api.episodes.bySeriesId([id]),
    {
      onSuccess: (data) => {
        cacheEpisodes(client, data);
      },
    }
  );
}

export function useEpisodeWantedPagination() {
  return usePaginationQuery([QueryKeys.Series, QueryKeys.Wanted], (param) =>
    api.episodes.wanted(param)
  );
}

export function useEpisodeBlacklist() {
  return useQuery(
    [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.Blacklist],
    () => api.episodes.blacklist()
  );
}

export function useEpisodeAddBlacklist() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.Blacklist],
    (param: {
      seriesId: number;
      episodeId: number;
      form: FormType.AddBlacklist;
    }) => {
      const { seriesId, episodeId, form } = param;
      return api.episodes.addBlacklist(seriesId, episodeId, form);
    },
    {
      onSuccess: (_, { seriesId, episodeId }) => {
        client.invalidateQueries([QueryKeys.Series, QueryKeys.Blacklist]);
        client.invalidateQueries([QueryKeys.Series, seriesId]);
      },
    }
  );
}

export function useEpisodeDeleteBlacklist() {
  const client = useQueryClient();
  return useMutation(
    [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.Blacklist],
    (param: { all?: boolean; form?: FormType.DeleteBlacklist }) =>
      api.episodes.deleteBlacklist(param.all, param.form),
    {
      onSuccess: (_, param) => {
        client.invalidateQueries([QueryKeys.Series, QueryKeys.Blacklist]);
      },
    }
  );
}

export function useEpisodeHistoryPagination() {
  return usePaginationQuery(
    [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.History],
    (param) => api.episodes.history(param)
  );
}

export function useEpisodeHistory(episodeId?: number) {
  return useQuery(
    [QueryKeys.Series, QueryKeys.Episodes, QueryKeys.History, episodeId],
    () => {
      if (episodeId) {
        return api.episodes.historyBy(episodeId);
      }
    }
  );
}
