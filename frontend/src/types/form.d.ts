declare namespace FormType {
  interface ModifyItem {
    id: number[];
    profileId: (number | null)[];
  }

  type SeriesAction = OneSeriesAction | SearchWantedAction;

  type MoviesAction = OneMovieAction | SearchWantedAction;

  interface OneMovieAction {
    action: "search-missing" | "scan-disk" | "sync";
    radarrId: number;
  }

  interface OneSeriesAction {
    action: "search-missing" | "scan-disk" | "sync";
    seriesId: number;
  }

  interface SearchWantedAction {
    action: "search-wanted";
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
    subtitlesId: number;
    type: "episode" | "movie";
    language: string;
    path: string | null;
    mediaTitle?: string;
    forced?: PythonBoolean;
    hi?: PythonBoolean;
    originalFormat?: PythonBoolean;
    reference?: string;
    maxOffsetSeconds?: string;
    noFixFramerate?: PythonBoolean;
    gss?: PythonBoolean;
  }

  interface DownloadSeries {
    episodePath: string;
    sceneName?: string;
    language: string;
    hi: boolean;
    forced: boolean;
    sonarrSeriesId: number;
    sonarrEpisodeId: number;
    title: string;
  }

  interface AddBlacklist {
    provider: string;
    subsId: string;
    language: Language.CodeType;
    subtitlesPath: string;
  }

  interface DeleteBlacklist {
    provider: string;
    subsId: string;
  }

  interface ManualDownload {
    language: string;
    hi: PythonBoolean;
    forced: PythonBoolean;
    provider: string;
    subtitle: unknown;
    originalFormat: PythonBoolean;
  }

  interface AddAnnouncementsDismiss {
    hash: number;
  }

  interface PlexSelectServer {
    machineIdentifier: string;
    name: string;
    uri: string;
    local: boolean;
    connections?: string[];
  }
}
