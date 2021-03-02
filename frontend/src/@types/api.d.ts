type LanguageCodeType = string;

interface Badge {
  value: number;
}

interface Language {
  code2: LanguageCodeType;
  name: string;
  hi?: boolean;
  forced?: boolean;
}

interface LanguagesProfileItem {
  id: number;
  audio_exclude: PythonBoolean;
  forced: PythonBoolean;
  hi: PythonBoolean;
  language: LanguageCodeType;
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

interface PathType {
  path: string;
  mapped_path: string;
  exist: boolean;
}

interface SubtitlePathType {
  subtitles_path: string;
  mapped_subtitles_path: string;
}

interface MonitoredType {
  monitored: boolean;
}

interface SubtitleType {
  subtitles: Subtitle[];
}

interface MissingSubtitleType {
  missing_subtitles: Subtitle[];
}

interface SceneNameType {
  sceneName?: string;
}

interface TagType {
  tags: string[];
}

interface SeriesIdType {
  sonarrSeriesId: number;
}

type EpisodeIdType = SeriesIdType & {
  sonarrEpisodeId: number;
};

interface EpisodeTitleType {
  seriesTitle: string;
  episodeTitle: string;
}

interface MovieIdType {
  radarrId: number;
}

interface TitleType {
  title: string;
}

interface AudioLanguageType {
  audio_language: Language[];
}

type BaseItem = PathType &
  TitleType &
  TagType &
  AudioLanguageType & {
    profileId?: number;
    fanart: string;
    overview: string;
    imdbId: string;
    alternativeTitles: string[];
    poster: string;
    year: string;
  };

type Series = BaseItem &
  SeriesIdType & {
    episodeFileCount: number;
    episodeMissingCount: number;
    seriesType: SonarrSeriesType;
    tvdbId: number;
  };

type Movie = BaseItem &
  MovieIdType &
  MonitoredType &
  SubtitleType &
  MissingSubtitleType &
  SceneNameType & {
    audio_codec: string;
    // movie_file_id: number;
    tmdbId: number;
  };

type Episode = PathType &
  TitleType &
  MonitoredType &
  EpisodeIdType &
  SubtitleType &
  MissingSubtitleType &
  SceneNameType &
  AudioLanguageType & {
    audio_codec: string;
    video_codec: string;
    season: number;
    episode: number;
    resolution: string;
    format: string;
    // episode_file_id: number;
  };

type WantedItem = MonitoredType &
  PathType &
  TagType &
  SceneNameType & {
    // failedAttempts?: any;
    hearing_impaired: boolean;
    missing_subtitles: Subtitle[];
  };

type WantedEpisode = WantedItem &
  EpisodeIdType &
  EpisodeTitleType & {
    episode_number: string;
    seriesType: SonarrSeriesType;
  };

type WantedMovie = WantedItem & MovieIdType & TitleType;

interface ItemHistoryType {
  language: Language;
  provider: string;
}

type BaseBlacklist = ItemHistoryType & {
  timestamp: string;
  subs_id: string;
};

type MovieBlacklist = BaseBlacklist & MovieIdType & TitleType;

type EpisodeBlacklist = BaseBlacklist &
  EpisodeTitleType &
  SeriesIdType & {
    episode_number: string;
  };

type BaseHistory = PathType &
  SubtitlePathType &
  TagType &
  MonitoredType &
  PathType &
  Partial<ItemHistoryType> & {
    action: number;
    // blacklisted: boolean;
    score?: string;
    // subs_id?: string;
    timestamp: string;
    description: string;
    upgradable: boolean;
  };

type EpisodeHistory = BaseHistory &
  EpisodeIdType &
  EpisodeTitleType & {
    episode_number: string;
  };

type MovieHistory = BaseHistory & MovieIdType & TitleType;

interface SearchResultType {
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

interface SubtitleInfo {
  filename: string;
  episode: number;
  season: number;
}
