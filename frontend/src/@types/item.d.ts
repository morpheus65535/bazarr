interface Badge {
  value: number;
}

interface Language {
  code2: string;
  name: string;
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

interface BasicItem {
  audio_language: Language[];
  exist: boolean;
  mapped_path: string;
  path: string;
  title: string;
}

// Temp Name
interface ExtendItem extends BasicItem {
  profileId?: number;
  fanart: string;
  overview: string;
  imdbId: string;
  languages: Language[];
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
  monitored: boolean;
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
  monitored: boolean;
  missing_subtitles: Subtitle[];
  subtitles: Subtitle[]; // FIX: Backend format
  format: string;
  episode_file_id: number;
}

interface WantedItem {
  exist: boolean;
  failedAttempts?: any;
  hearing_impaired: boolean;
  mapped_path: string;
  missing_subtitles: Subtitle[];
  monitored: boolean;
  path: string;
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
