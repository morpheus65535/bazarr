namespace FormType {
  interface ModifyItem {
    id: number[];
    profileid: (number | undefined)[];
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
    // code2
    language: string;
    forced: boolean;
    hi: boolean;
    path: string;
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
