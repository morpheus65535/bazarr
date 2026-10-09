import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

export const useSystemProviders = (history?: boolean) =>
  useQuery({
    queryKey: [QueryKeys.System, QueryKeys.Providers, history ?? false],
    queryFn: () => api.providers.providers(history),
  });

export const useMoviesProvider = (radarrId?: number) =>
  useQuery({
    queryKey: [
      QueryKeys.System,
      QueryKeys.Providers,
      QueryKeys.Movies,
      radarrId,
    ],

    queryFn: () => {
      if (radarrId) {
        return api.providers.movies(radarrId);
      }

      return [];
    },

    staleTime: 0,
  });

export const useEpisodesProvider = (episodeId?: number) =>
  useQuery({
    queryKey: [
      QueryKeys.System,
      QueryKeys.Providers,
      QueryKeys.Episodes,
      episodeId,
    ],

    queryFn: () => {
      if (episodeId) {
        return api.providers.episodes(episodeId);
      }

      return [];
    },

    staleTime: 0,
  });

export const useResetProvider = () => {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [QueryKeys.System, QueryKeys.Providers],
    mutationFn: () => api.providers.reset(),

    onSuccess: () => {
      client.invalidateQueries({
        queryKey: [QueryKeys.System, QueryKeys.Providers],
      });
    },
  });
};

export const useDownloadEpisodeSubtitles = () => {
  const client = useQueryClient();

  return useMutation({
    mutationKey: [
      QueryKeys.System,
      QueryKeys.Providers,
      QueryKeys.Subtitles,
      QueryKeys.Episodes,
    ],

    mutationFn: (param: {
      seriesId: number;
      episodeId: number;
      form: FormType.ManualDownload;
    }) =>
      api.providers.downloadEpisodeSubtitle(
        param.seriesId,
        param.episodeId,
        param.form,
      ),

    onSuccess: (_, param) => {
      client.invalidateQueries({
        queryKey: [QueryKeys.Series, param.seriesId],
      });
    },
  });
};

export const useDownloadMovieSubtitles = () => {
  const client = useQueryClient();

  return useMutation({
    mutationKey: [
      QueryKeys.System,
      QueryKeys.Providers,
      QueryKeys.Subtitles,
      QueryKeys.Movies,
    ],

    mutationFn: (param: { radarrId: number; form: FormType.ManualDownload }) =>
      api.providers.downloadMovieSubtitle(param.radarrId, param.form),

    onSuccess: (_, param) => {
      client.invalidateQueries({
        queryKey: [QueryKeys.Movies, param.radarrId],
      });
    },
  });
};
