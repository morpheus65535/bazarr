// Python
type PythonBoolean = "True" | "False";

// Sonarr
type SonarrSeriesType = "Standard" | "Daily" | "Anime";

// Helper
interface DataWrapper<T> {
  data: T;
}

// Badges
interface SeriesBadge {
  missing_episodes: number;
}

interface MoviesBadge {
  missing_movies: number;
}

interface ProvidersBadge {
  throttled_providers: number;
}

// System
interface Language {
  code2?: string;
  code3?: string;
  code3b?: string;
  enabled: boolean;
  name: string;
}

interface BasicItem {
  DT_RowId: string;
  alternateTitles: [string];
  audio_language: SeriesLanguage;
  exist: true;
  fanart: string;
  forced: PythonBoolean;
  hearing_impaired: PythonBoolean;
  imdbId: string;
  languages: [SeriesLanguage] | string;
  mapped_path: string;
  overview: string;
  path: string;
  poster: string;
  sortTitle: string;
  tags: [string];
  title: string;
  year: string;
}

// Series
interface SeriesLanguage {
  code2: string;
  code3: string;
  name: string;
}

interface SubtitleInfo extends SeriesLanguage {
  forced: boolean;
  hi: boolean;
}

interface Series extends BasicItem {
  episodeFileCount: number;
  episodeMissingCount: number;
  imdbId: string;
  seriesType: SonarrSeriesType;
  sonarrSeriesId: number;
  tvdbId: number;
}

interface WantedSeries {
  episodeTitle: string;
  episode_number: string;
  exist: boolean;
  failedAttempts?: any;
  hearing_impaired: PythonBoolean;
  mapped_path: string;
  missing_subtitles: SubtitleInfo[];
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

// Movie
interface Movie extends BasicItem {
  audio_codec: string;
  missing_subtitles: SubtitleInfo[];
  monitored: PythonBoolean;
  movie_file_id: number;
  radarrId: number;
  tmdbId: number;
}

// System
interface SystemStatusResult {
  bazarr_config_directory: string;
  bazarr_directory: string;
  bazarr_version: string;
  operating_system: string;
  python_version: string;
  radarr_version: string;
  sonarr_version: string;
}

interface SystemTaskResult {
  DT_RowId: string;
  interval: string;
  job_id: string;
  job_running: boolean;
  name: string;
  next_run_in: string;
  next_run_time: string;
}
