import { useMutation, useQuery, useQueryClient } from "react-query";
import { QueryKeys } from "../queries/keys";
import api from "../raw";

export function useSubtitleAction() {
  const client = useQueryClient();
  interface Param {
    action: string;
    form: FormType.ModifySubtitle;
  }
  return useMutation(
    (param: Param) => api.subtitles.modify(param.action, param.form),
    {
      onSuccess: () => {
        client.invalidateQueries([QueryKeys.History]);
      },
    }
  );
}

export function useEpisodeSubtitleModification() {
  const client = useQueryClient();

  interface Param<T> {
    seriesId: number;
    episodeId: number;
    form: T;
  }

  const download = useMutation(
    (param: Param<FormType.Subtitle>) =>
      api.episodes.downloadSubtitles(
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

  const remove = useMutation(
    (param: Param<FormType.DeleteSubtitle>) =>
      api.episodes.deleteSubtitles(param.seriesId, param.episodeId, param.form),
    {
      onSuccess: (_, param) => {
        client.invalidateQueries([QueryKeys.Series, param.seriesId]);
      },
    }
  );

  const upload = useMutation(
    (param: Param<FormType.UploadSubtitle>) =>
      api.episodes.uploadSubtitles(param.seriesId, param.episodeId, param.form),
    {
      onSuccess: (_, { seriesId }) => {
        client.invalidateQueries([QueryKeys.Series, seriesId]);
      },
    }
  );

  return { download, remove, upload };
}

export function useMovieSubtitleModification() {
  const client = useQueryClient();

  interface Param<T> {
    radarrId: number;
    form: T;
  }

  const download = useMutation(
    (param: Param<FormType.Subtitle>) =>
      api.movies.downloadSubtitles(param.radarrId, param.form),
    {
      onSuccess: (_, param) => {
        client.invalidateQueries([QueryKeys.Movies, param.radarrId]);
      },
    }
  );

  const remove = useMutation(
    (param: Param<FormType.DeleteSubtitle>) =>
      api.movies.deleteSubtitles(param.radarrId, param.form),
    {
      onSuccess: (_, param) => {
        client.invalidateQueries([QueryKeys.Movies, param.radarrId]);
      },
    }
  );

  const upload = useMutation(
    (param: Param<FormType.UploadSubtitle>) =>
      api.movies.uploadSubtitles(param.radarrId, param.form),
    {
      onSuccess: (_, { radarrId }) => {
        client.invalidateQueries([QueryKeys.Movies, radarrId]);
      },
    }
  );

  return { download, remove, upload };
}

export function useSubtitleInfos(names: string[]) {
  return useQuery([QueryKeys.Subtitles, QueryKeys.Infos, names], () =>
    api.subtitles.info(names)
  );
}
