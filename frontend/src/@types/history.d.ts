interface BaseHistory {
  action: number;
  blacklisted: boolean;
  exist: boolean;
  language?: Language;
  mapped_path: string;
  mapped_subtitles_path: string;
  provider?: string;
  // raw_timestamp: number;
  score?: string; // TODO: Fix
  subs_id?: string;
  subtitles_path: string;
  tags: string[];
  timestamp: string;
}

interface EpisodeHistory extends BaseHistory {
  sonarrEpisodeId: number;
  sonarrSeriesId: number;
  video_path: string;
}

interface ExtendHistory extends BaseHistory {
  description: string;
  monitored: boolean;
  upgradable: boolean;
}

interface SeriesHistory extends ExtendHistory {
  episodeTitle: string;
  path: string;
  episode_number: string;
  seriesTitle: string;
  sonarrEpisodeId: number;
  sonarrSeriesId: number;
}

interface MovieHistory extends ExtendHistory {
  title: string;
  radarrId: number;
  video_path: string;
}
