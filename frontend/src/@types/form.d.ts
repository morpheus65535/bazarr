declare namespace FormType {
  interface ModifyItem {
    id: number[];
    profileid: (number | null)[];
  }

  type SeriesAction =
    | OneSerieAction
    | SearchWantedAction
    | SeriesMonitoredAction;

  type EpisodesAction = EpisodeMonitoredAction;

  type MoviesAction =
    | OneMovieAction
    | SearchWantedAction
    | MovieMonitoredAction;

  interface OneMovieAction {
    action: "search-missing" | "refresh";
    movieid: number;
  }

  interface OneSerieAction {
    action: "search-missing" | "refresh";
    seriesid: number;
  }

  interface SearchWantedAction {
    action: "search-wanted";
  }

  interface SeriesMonitoredAction {
    seriesid: number;
    action: "monitored";
    value: boolean;
  }

  interface EpisodeMonitoredAction {
    episodeid: number;
    action: "monitored";
    value: boolean;
  }

  interface MovieMonitoredAction {
    movieid: number;
    action: "monitored";
    value: boolean;
  }

  interface Subtitle {
    language: string;
    hi: boolean;
    forced: boolean;
  }

  interface UploadSubtitle extends Subtitle {
    file: File;
  }

  interface DeleteSubtitle extends Subtitle {
    path: string;
  }

  interface ModifySubtitle {
    id: number;
    type: "episode" | "movie";
    language: string;
    path: string;
  }

  interface DownloadSeries {
    episodePath: string;
    sceneName?: string;
    language: string;
    hi: boolean;
    forced: boolean;
    seriesId: number;
    episodeId: number;
    title: string;
  }

  interface AddBlacklist {
    provider: string;
    subs_id: string;
    language: Language.CodeType;
    subtitles_path: string;
  }

  interface DeleteBlacklist {
    provider: string;
    subs_id: string;
  }

  interface ManualDownload {
    language: string;
    hi: PythonBoolean;
    forced: PythonBoolean;
    provider: string;
    subtitle: any;
  }
}
