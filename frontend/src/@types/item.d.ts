interface Badge {
  value: number;
}

interface Language {
  code2: string;
  name: string;
  hi?: boolean;
  forced?: boolean;
}

interface LanguagesProfileItem {
  id: number;
  audio_exclude: PythonBoolean;
  forced: PythonBoolean;
  hi: PythonBoolean;
  language: string;
}

interface LanguagesProfile {
  name: string;
  profileId: number;
  cutoff: number | null;
  items: LanguagesProfileItem[];
}

interface Subtitle extends Language {
  forced: boolean;
  hi: boolean;
  path: string | null;
}

interface BaseItem {
  audio_language: Language[];
  exist: boolean;
  mapped_path: string;
  // path: string;
  title: string;
}

// Temp Name
interface ExtendItem extends BaseItem {
  profileId?: number;
  fanart: string;
  overview: string;
  imdbId: string;
  languages: Language[];
  alternativeTitles: string[];
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
  monitored: boolean;
  movie_file_id: number;
  radarrId: number;
  tmdbId: number;
  sceneName?: string;
}

interface Episode extends BaseItem {
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
  monitored: boolean;
  missing_subtitles: Subtitle[];
  subtitles: Subtitle[]; // FIX: Backend format
  format: string;
  episode_file_id: number;
  scene_name?: string;
}

interface WantedItem {
  exist: boolean;
  failedAttempts?: any;
  hearing_impaired: boolean;
  mapped_path: string;
  missing_subtitles: Subtitle[];
  monitored: boolean;
  // path: string;
  tags: string[];
}

interface WantedEpisode extends WantedItem {
  episodeTitle: string;
  episode_number: string;
  // scene_name?: any;
  seriesTitle: string;
  seriesType: SonarrSeriesType;
  sonarrEpisodeId: number;
  sonarrSeriesId: number;
}

interface WantedMovie extends WantedItem {
  radarrId: number;
  // sceneName?: any;
  title: string;
}

interface SubtitleNameInfo {
  filename: string;
  episode: number;
  season: number;
}

interface BlacklistItem {
  language: Language;
  provider: string;
  timestamp: string;
  raw_timestamp: number;
  subs_id: string;
}

interface MovieBlacklist extends BlacklistItem {
  radarrId: number;
  title: string;
}

interface SeriesBlacklist extends BlacklistItem {
  episodeTitle: string;
  episode_number: string;
  seriesTitle: string;
  sonarrSeriesId: number;
}

interface ManualSearchResult {
  matches: string[];
  dont_matches: string[];
  language: string;
  forced: PythonBoolean;
  hearing_impaired: PythonBoolean;
  orig_score: number;
  provider: string;
  release_info: string[];
  score: number;
  score_without_hash: number;
  // TODO: Remove this on server side
  subtitle: any;
  uploader?: string;
  url?: string;
}

interface ReleaseInfo {
  current: boolean;
  date: string;
  name: string;
  prerelease: boolean;
  body: string[];
}
