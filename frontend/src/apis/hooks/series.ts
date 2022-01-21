import { useQuery } from "react-query";
import { createSeriesId } from "../../utilities";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useSeriesByIds(ids: number[]) {
  return useQuery([QueryKeys.Series, ...ids], () => api.series.series(ids));
}

export function useSeries() {
  return useQuery([QueryKeys.Series], () => api.series.series());
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
