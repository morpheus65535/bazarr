interface ItemModifyForm {
  profileid?: number;
}

interface SubtitleForm {
  language: string;
  hi: boolean;
  forced: boolean;
}

interface SubtitleUploadForm extends SubtitleForm {
  file: File;
}

interface SubtitleDeleteForm extends SubtitleForm {
  path: string;
}

interface SeriesDownloadForm {
  episodePath: string;
  sceneName?: string;
  language: string;
  hi: boolean;
  forced: boolean;
  sonarrSeriesId: number;
  sonarrEpisodeId: number;
  title: string;
}
