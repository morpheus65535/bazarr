import { useQuery } from "react-query";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useEpisodeByIds(ids: number[]) {
  return useQuery([QueryKeys.Episodes, ...ids], () =>
    api.episodes.byEpisodeId(ids)
  );
}

export function useEpisodeBySeriesId(ids: number[]) {
  return useQuery([QueryKeys.Episodes, QueryKeys.Series, ...ids], () =>
    api.episodes.bySeriesId(ids)
  );
}

export function useEpisodeBlacklist() {
  return useQuery([QueryKeys.Episodes, QueryKeys.Blacklist], () =>
    api.episodes.blacklist()
  );
}
