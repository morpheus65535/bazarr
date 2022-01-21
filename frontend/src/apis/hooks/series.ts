import { useQuery } from "react-query";
import { createEpisodeId, createSeriesId } from "../../utilities";
import QueryKeys from "../queries/keys";
import api from "../raw";

export function useSeriesByIds(ids: number[]) {
  return useQuery([QueryKeys.series, ...ids], () => api.series.series(ids));
}

export function useSeries() {
  return useQuery(QueryKeys.series, () => api.series.series());
}

export function useEpisodeByIds(ids: number[]) {
  const keys = ids.map(createEpisodeId);
  return useQuery([QueryKeys.episodes, ...keys], () =>
    api.episodes.byEpisodeId(ids)
  );
}

export function useEpisodeBySeriesId(ids: number[]) {
  const keys = ids.map(createSeriesId);
  return useQuery([QueryKeys.episodes, ...keys], () =>
    api.episodes.bySeriesId(ids)
  );
}

export function useEpisodeBlacklist() {
  return useQuery([QueryKeys.episodes, { type: "blacklist" }], () =>
    api.episodes.blacklist()
  );
}
