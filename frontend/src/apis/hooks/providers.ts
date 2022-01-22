import { useMutation, useQuery, useQueryClient } from "react-query";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useSystemProviders(history?: boolean) {
  return useQuery(
    [QueryKeys.System, QueryKeys.Providers, history ?? false],
    () => api.providers.providers(history)
  );
}

export function useMoviesProvider(radarrId?: number) {
  return useQuery(
    [QueryKeys.System, QueryKeys.Providers, QueryKeys.Movies, radarrId],
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
  return useQuery(
    [QueryKeys.System, QueryKeys.Providers, QueryKeys.Episodes, episodeId],
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
  return useMutation(
    [QueryKeys.System, QueryKeys.Providers],
    () => api.providers.reset(),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.System, QueryKeys.Providers]);
      },
    }
  );
}

export function useDownloadEpisodeSubtitles() {
  const client = useQueryClient();

  return useMutation(
    [
      QueryKeys.System,
      QueryKeys.Providers,
      QueryKeys.Subtitles,
      QueryKeys.Episodes,
    ],
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
        client.invalidateQueries([QueryKeys.Series, param.seriesId]);
      },
    }
  );
}

export function useDownloadMovieSubtitles() {
  const client = useQueryClient();

  return useMutation(
    [
      QueryKeys.System,
      QueryKeys.Providers,
      QueryKeys.Subtitles,
      QueryKeys.Movies,
    ],
    (param: { radarrId: number; form: FormType.ManualDownload }) =>
      api.providers.downloadMovieSubtitle(param.radarrId, param.form),
    {
      onSuccess: (_, param) => {
        client.invalidateQueries([QueryKeys.Movies, param.radarrId]);
      },
    }
  );
}
