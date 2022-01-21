import { useQuery, useQueryClient } from "react-query";
import { createSeriesId } from "../../utilities";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useSeriesByIds(ids: number[]) {
  const client = useQueryClient();
  return useQuery([QueryKeys.Series, ...ids], () => api.series.series(ids), {
    onSuccess: (data) => {
      data.forEach((v) => {
        client.setQueryData([QueryKeys.Series, v.sonarrSeriesId], data);
      });
    },
  });
}

export function useSeriesById(id: number) {
  return useQuery([QueryKeys.Series, id], async () => {
    const response = await api.series.series([id]);
    return response.length > 0 ? response[0] : undefined;
  });
}

export function useSeries() {
  const client = useQueryClient();
  return useQuery([QueryKeys.Series, "all-items"], () => api.series.series(), {
    onSuccess: (data) => {
      data.forEach((v) => {
        client.setQueryData([QueryKeys.Series, v.sonarrSeriesId], data);
      });
    },
  });
}

export function useEpisodeByIds(ids: number[]) {
  return useQuery([QueryKeys.Episodes, ...ids], () =>
    api.episodes.byEpisodeId(ids)
  );
}

export function useEpisodeBySeriesId(ids: number[]) {
  const keys = ids.map(createSeriesId);
  return useQuery([QueryKeys.Series, QueryKeys.Episodes, ...keys], () =>
    api.episodes.bySeriesId(ids)
  );
}

export function useEpisodeBlacklist() {
  return useQuery([QueryKeys.Episodes, QueryKeys.Blacklist], () =>
    api.episodes.blacklist()
  );
}
