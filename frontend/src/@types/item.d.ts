interface ExtendLanguage {
  code2?: string;
  code3?: string;
  code3b?: string;
  enabled: boolean;
  name: string;
}

interface Language {
  code2: string;
  code3: string;
  name: string;
}

interface Subtitle extends Language {
  forced: boolean;
  hi: boolean;
  path: string | null;
}

interface BasicItem {
  // DT_RowId: string;
  audio_language: Language;
  exist: boolean;
  mapped_path: string;
  path: string;
  title: string;
}

// Temp Name
interface ExtendItem extends BasicItem {
  fanart: string;
  forced: PythonBoolean;
  overview: string;
  hearing_impaired: PythonBoolean;
  imdbId: string;
  languages: Language[] | string;
  alternateTitles: string[];
  poster: string;
  sortTitle: string;
  tags: string[];
  year: string;
}

interface Series extends ExtendItem {
  episodeFileCount: number;
  episodeMissingCount: number;
  imdbId: string;
  seriesType: SonarrSeriesType;
  sonarrSeriesId: number;
  tvdbId: number;
}

interface Movie extends ExtendItem {
  audio_codec: string;
  subtitles: Subtitle[];
  missing_subtitles: Subtitle[];
  monitored: PythonBoolean;
  movie_file_id: number;
  radarrId: number;
  tmdbId: number;
}

interface Episode extends BasicItem {
  audio_codec: string;
  video_codec: string;
  // desired_languages: string[];
  // failedAttempts: string[];
  sonarrSeriesId: number;
  sonarrEpisodeId: number;
  season: number;
  episode: number;
  scene_name: string;
  resolution: string;
  monitored: PythonBoolean;
  missing_subtitles: Subtitle[];
  format: string;
  episode_file_id: number;
}

interface WantedEpisode {
  episodeTitle: string;
  episode_number: string;
  exist: boolean;
  failedAttempts?: any;
  hearing_impaired: PythonBoolean;
  mapped_path: string;
  missing_subtitles: Subtitle[];
  monitored: PythonBoolean;
  path: string;
  scene_name?: any;
  seriesTitle: string;
  seriesType: SonarrSeriesType;
  sonarrEpisodeId: number;
  sonarrSeriesId: number;
  tags: string[];
}

interface SeriesSubDownloadRequest {
  episodePath: string;
  sceneName?: string;
  language: string;
  hi: boolean;
  forced: boolean;
  sonarrSeriesId: number;
  sonarrEpisodeId: number;
  title: string;
}
