import { QueryClient, useQuery, useQueryClient } from "react-query";
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
    [QueryKeys.Episodes, ids],
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

export function useEpisodeBlacklist() {
  return useQuery([QueryKeys.Episodes, QueryKeys.Blacklist], () =>
    api.episodes.blacklist()
  );
}
