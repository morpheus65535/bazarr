enum HistoryAction {
  Download = 1,
  Upload = 4,
  Sync = 5,
}

interface BasicHistory {
  action: HistoryAction;
  blacklisted: boolean;
  description: string;
  exist: boolean;
  language: ExtendLanguage;
  mapped_path: string;
  mapped_subtitles_path: string;
  monitored: PythonBoolean;
  path: string;
  provider?: string;
  raw_timestamp: number;
  score?: string; // TODO: Fix
  subs_id?: string;
  subtitles_path: string;
  tags: string[];
  timestamp: string;
  upgradable: boolean;
}

interface SeriesHistory extends BasicHistory {
  episodeTitle: string;
  episode_number: string;
  seriesTitle: string;
  sonarrEpisodeId: number;
  sonarrSeriesId: number;
}

interface MovieHistory extends BasicHistory {
  title: string;
  radarrId: number;
  video_path: string;
}
