declare namespace FormType {
  interface ModifyItem {
    id: number[];
    profileid: (number | null)[];
  }

  type SeriesAction = OneSeriesAction | SearchWantedAction;

  type MoviesAction = OneMovieAction | SearchWantedAction;

  interface OneMovieAction {
    action: "search-missing" | "scan-disk" | "sync";
    radarrid: number;
  }

  interface OneSeriesAction {
    action: "search-missing" | "scan-disk" | "sync";
    seriesid: number;
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
    type: "episode" | "movie";
    language: string;
    path: string;
    forced?: PythonBoolean;
    hi?: PythonBoolean;
    original_format?: PythonBoolean;
    reference?: string;
    max_offset_seconds?: string;
    no_fix_framerate?: PythonBoolean;
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
    subtitle: unknown;
    original_format: PythonBoolean;
  }

  interface AddAnnouncementsDismiss {
    hash: number;
  }

  interface PlexSelectServer {
    machineIdentifier: string;
    name: string;
    uri: string;
    local: boolean;
  }
}
