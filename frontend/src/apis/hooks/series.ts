import { useQuery } from "react-query";
import { createEpisodeId, createSeriesId } from "../../utilities";
import QueryKeys from "../queries/keys";
import api from "../raw";

export function useSeriesByIds(ids: number[]) {
  const keys = ids.map(createSeriesId);
  return useQuery([QueryKeys.series, ...keys], () => api.series.series(ids));
}

export function useSeries() {
  return useQuery(QueryKeys.series, () => api.series.series());
}

export function useEpisodeByIds(ids: number[]) {
  const keys = ids.map(createEpisodeId);
  return useQuery([QueryKeys.series, QueryKeys.episodes, ...keys], () =>
    api.episodes.byEpisodeId(ids)
  );
}

export function useEpisodeBySeriesId(ids: number[]) {
  const keys = ids.map(createSeriesId);
  return useQuery([QueryKeys.series, QueryKeys.episodes, ...keys], () =>
    api.episodes.bySeriesId(ids)
  );
}

export function useEpisodeBlacklist() {
  return useQuery(
    [QueryKeys.series, QueryKeys.episodes, QueryKeys.blacklist],
    () => api.episodes.blacklist()
  );
}
