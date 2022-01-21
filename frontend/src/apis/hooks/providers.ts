import { useMutation, useQuery, useQueryClient } from "react-query";
import { createEpisodeId, createMovieId, createSeriesId } from "src/utilities";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useSystemProviders(history?: boolean) {
  return useQuery(
    [QueryKeys.System, QueryKeys.Providers, history ?? false],
    () => api.providers.providers(history)
  );
}

export function useMoviesProvider(radarrId?: number) {
  const movieKey = createMovieId(radarrId ?? -1);
  return useQuery(
    [QueryKeys.System, QueryKeys.Providers, movieKey],
    () => {
      if (radarrId) {
        return api.providers.movies(radarrId);
      }
    },
    {
      staleTime: Infinity,
    }
  );
}

export function useEpisodesProvider(episodeId?: number) {
  const episodeKey = createEpisodeId(episodeId ?? -1);
  return useQuery(
    [QueryKeys.System, QueryKeys.Providers, episodeKey],
    () => {
      if (episodeId) {
        return api.providers.episodes(episodeId);
      }
    },
    {
      staleTime: Infinity,
    }
  );
}

export function useResetProvider() {
  const client = useQueryClient();
  return useMutation(() => api.providers.reset(), {
    onSuccess: () => {
      client.invalidateQueries([QueryKeys.System, QueryKeys.Providers]);
    },
  });
}

export function useDownloadEpisodeSubtitles() {
  const client = useQueryClient();

  return useMutation(
    (param: {
      seriesId: number;
      episodeId: number;
      form: FormType.ManualDownload;
    }) =>
      api.providers.downloadEpisodeSubtitle(
        param.seriesId,
        param.episodeId,
        param.form
      ),
    {
      onSuccess: (_, param) => {
        const seriesKey = createSeriesId(param.seriesId);
        const episodeKey = createEpisodeId(param.episodeId);

        client.invalidateQueries(seriesKey);
        client.invalidateQueries(episodeKey);
      },
    }
  );
}

export function useDownloadMovieSubtitles() {
  const client = useQueryClient();

  return useMutation(
    (param: { radarrId: number; form: FormType.ManualDownload }) =>
      api.providers.downloadMovieSubtitle(param.radarrId, param.form),
    {
      onSuccess: (_, param) => {
        const movieKey = createSeriesId(param.radarrId);

        client.invalidateQueries(movieKey);
      },
    }
  );
}
