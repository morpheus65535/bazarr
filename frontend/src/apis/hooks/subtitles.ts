import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "@/apis/queries/keys";
import api from "@/apis/raw";

export const useSubtitleAction = () => {
  const client = useQueryClient();
  interface Param {
    action: string;
    form: FormType.ModifySubtitle;
  }
  return useMutation({
    mutationKey: [QueryKeys.Subtitles],
    mutationFn: (param: Param) =>
      api.subtitles.modify(param.action, param.form),

    onSuccess: (_, param) => {
      client.invalidateQueries({
        queryKey: [QueryKeys.History],
      });

      // TODO: Query less
      const { type, id } = param.form;
      if (type === "episode") {
        client.invalidateQueries({
          queryKey: [QueryKeys.Series, id],
        });
      } else {
        client.invalidateQueries({
          queryKey: [QueryKeys.Movies, id],
        });
      }
    },
  });
};

export const useEpisodeSubtitleModification = () => {
  const client = useQueryClient();

  interface Param<T> {
    seriesId: number;
    episodeId: number;
    form: T;
  }

  const download = useMutation({
    mutationKey: [QueryKeys.Subtitles, QueryKeys.Episodes],

    mutationFn: (param: Param<FormType.Subtitle>) =>
      api.episodes.downloadSubtitles(
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

  const remove = useMutation({
    mutationKey: [QueryKeys.Subtitles, QueryKeys.Episodes],

    mutationFn: (param: Param<FormType.DeleteSubtitle>) =>
      api.episodes.deleteSubtitles(param.seriesId, param.episodeId, param.form),

    onSuccess: (_, param) => {
      client.invalidateQueries({
        queryKey: [QueryKeys.Series, param.seriesId],
      });
    },
  });

  const upload = useMutation({
    mutationKey: [QueryKeys.Subtitles, QueryKeys.Episodes],

    mutationFn: (param: Param<FormType.UploadSubtitle>) =>
      api.episodes.uploadSubtitles(param.seriesId, param.episodeId, param.form),

    onSuccess: (_, { seriesId }) => {
      client.invalidateQueries({
        queryKey: [QueryKeys.Series, seriesId],
      });
    },
  });

  return { download, remove, upload };
};

export const useSportsSubtitleModification = () => {
  const client = useQueryClient();

  interface Param<T> {
    leagueId: number;
    eventId: number;
    form: T;
  }

  const invalidate = (leagueId: number) => {
    void client.invalidateQueries({
      queryKey: [QueryKeys.SportsLeagues, leagueId],
    });
  };

  const download = useMutation({
    mutationKey: [QueryKeys.Subtitles, QueryKeys.SportsEvents],

    mutationFn: (param: Param<FormType.Subtitle>) =>
      api.sports.downloadSubtitles(param.leagueId, param.eventId, param.form),

    onSuccess: (_, param) => invalidate(param.leagueId),
  });

  const remove = useMutation({
    mutationKey: [QueryKeys.Subtitles, QueryKeys.SportsEvents],

    mutationFn: (param: Param<FormType.DeleteSubtitle>) =>
      api.sports.deleteSubtitles(param.leagueId, param.eventId, param.form),

    onSuccess: (_, param) => invalidate(param.leagueId),
  });

  const upload = useMutation({
    mutationKey: [QueryKeys.Subtitles, QueryKeys.SportsEvents],

    mutationFn: (param: Param<FormType.UploadSubtitle>) =>
      api.sports.uploadSubtitles(param.leagueId, param.eventId, param.form),

    onSuccess: (_, { leagueId }) => invalidate(leagueId),
  });

  return { download, remove, upload };
};

export const useMovieSubtitleModification = () => {
  const client = useQueryClient();

  interface Param<T> {
    radarrId: number;
    form: T;
  }

  const download = useMutation({
    mutationKey: [QueryKeys.Subtitles, QueryKeys.Movies],

    mutationFn: (param: Param<FormType.Subtitle>) =>
      api.movies.downloadSubtitles(param.radarrId, param.form),

    onSuccess: (_, param) => {
      client.invalidateQueries({
        queryKey: [QueryKeys.Movies, param.radarrId],
      });
    },
  });

  const remove = useMutation({
    mutationKey: [QueryKeys.Subtitles, QueryKeys.Movies],

    mutationFn: (param: Param<FormType.DeleteSubtitle>) =>
      api.movies.deleteSubtitles(param.radarrId, param.form),

    onSuccess: (_, param) => {
      client.invalidateQueries({
        queryKey: [QueryKeys.Movies, param.radarrId],
      });
    },
  });

  const upload = useMutation({
    mutationKey: [QueryKeys.Subtitles, QueryKeys.Movies],

    mutationFn: (param: Param<FormType.UploadSubtitle>) =>
      api.movies.uploadSubtitles(param.radarrId, param.form),

    onSuccess: (_, { radarrId }) => {
      client.invalidateQueries({
        queryKey: [QueryKeys.Movies, radarrId],
      });
    },
  });

  return { download, remove, upload };
};

export const useSubtitleInfos = (names: string[]) =>
  useQuery({
    queryKey: [QueryKeys.Subtitles, QueryKeys.Infos, names],

    queryFn: () => api.subtitles.info(names),
  });

export const useSubtitleContents = (subtitlePath: string) =>
  useQuery({
    queryKey: [QueryKeys.Subtitles, subtitlePath],
    queryFn: () => api.subtitles.contents(subtitlePath),
    staleTime: Infinity,
  });

export const useRefTracksByEpisodeId = (
  subtitlesPath: string,
  sonarrEpisodeId: number,
  isEpisode: boolean,
) =>
  useQuery({
    queryKey: [
      QueryKeys.Episodes,
      sonarrEpisodeId,
      QueryKeys.Subtitles,
      subtitlesPath,
    ],
    queryFn: () =>
      api.subtitles.getRefTracksByEpisodeId(subtitlesPath, sonarrEpisodeId),
    enabled: isEpisode,
  });

export const useRefTracksByMovieId = (
  subtitlesPath: string,
  radarrMovieId: number,
  isMovie: boolean,
) =>
  useQuery({
    queryKey: [
      QueryKeys.Movies,
      radarrMovieId,
      QueryKeys.Subtitles,
      subtitlesPath,
    ],
    queryFn: () =>
      api.subtitles.getRefTracksByMovieId(subtitlesPath, radarrMovieId),
    enabled: isMovie,
  });
