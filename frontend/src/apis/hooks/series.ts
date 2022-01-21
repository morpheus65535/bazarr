import { useQuery } from "react-query";
import { createEpisodeId, createSeriesId } from "../../utilities";
import api from "../raw";

export function useSeriesByIds(ids: number[]) {
  const keys = ids.map(createSeriesId);
  return useQuery(["series", ...keys], () => api.series.series(ids));
}

export function useSeries() {
  return useQuery("series", () => api.series.series());
}

export function useEpisodeByIds(ids: number[]) {
  const keys = ids.map(createEpisodeId);
  return useQuery(["series", "episodes", ...keys], () =>
    api.episodes.byEpisodeId(ids)
  );
}

export function useEpisodeBySeriesId(ids: number[]) {
  const keys = ids.map(createSeriesId);
  return useQuery(["series", "episodes", ...keys], () =>
    api.episodes.bySeriesId(ids)
  );
}

export function useEpisodeBlacklist() {
  return useQuery(["series", "episodes", "blacklist"], () =>
    api.episodes.blacklist()
  );
}
