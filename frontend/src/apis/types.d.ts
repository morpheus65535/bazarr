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

// Series
interface SeriesLanguage {
  code2: string;
  code3: string;
  name: string;
}

interface Series {
  DT_RowId: string;
  alternateTitles: [string];
  audio_language: SeriesLanguage;
  episodeFileCount: number;
  episodeMissingCount: number;
  exist: true;
  fanart: string;
  forced: PythonBoolean;
  hearing_impaired: PythonBoolean;
  imdbId: string;
  languages: [SeriesLanguage];
  mapped_path: string;
  overview: string;
  path: string;
  poster: string;
  seriesType: SonarrSeriesType;
  sonarrSeriesId: number;
  sortTitle: string;
  tags: [string];
  title: string;
  tvdbId: number;
  year: string;
}

// System
interface SystemStatusResult {
  bazarr_config_directory: string
  bazarr_directory: string
  bazarr_version: string
  operating_system: string
  python_version: string
  radarr_version: string
  sonarr_version: string
}
