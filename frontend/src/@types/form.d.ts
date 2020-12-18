interface ItemModifyForm {
  languages: string[];
  hi: boolean;
  forced: boolean;
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
