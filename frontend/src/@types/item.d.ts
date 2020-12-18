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
  audio_language: Language;
  exist: boolean;
  mapped_path: string;
  path: string;
  title: string;
}

// Temp Name
interface ExtendItem extends BasicItem {
  fanart: string;
  forced: boolean;
  overview: string;
  hearing_impaired: boolean;
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
