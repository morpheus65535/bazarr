import { useQuery } from "react-query";
import { EpisodesApi, SeriesApi } from "..";
import { createEpisodeId, createSeriesId } from "../../utilities";

export function useSeriesByIds(ids: number[]) {
  const keys = ids.map(createSeriesId);
  return useQuery(["series", ...keys], () => SeriesApi.series(ids));
}

export function useSeries() {
  return useQuery("series", () => SeriesApi.series());
}

export function useEpisodeByIds(ids: number[]) {
  const keys = ids.map(createEpisodeId);
  return useQuery(["series", "episodes", ...keys], () =>
    EpisodesApi.byEpisodeId(ids)
  );
}

export function useEpisodeBySeriesId(ids: number[]) {
  const keys = ids.map(createSeriesId);
  return useQuery(["series", "episodes", ...keys], () =>
    EpisodesApi.bySeriesId(ids)
  );
}

export function useEpisodeBlacklist() {
  return useQuery(["series", "episodes", "blacklist"], () =>
    EpisodesApi.blacklist()
  );
}
