interface Badge {
  episodes: number;
  movies: number;
  providers: number;
  status: number;
}

declare namespace Language {
  type CodeType = string;
  interface Server {
    code2: CodeType;
    name: string;
    enabled: boolean;
  }

  interface Info {
    code2: CodeType;
    name: string;
    hi?: boolean;
    forced?: boolean;
  }

  interface ProfileItem {
    id: number;
    audio_exclude: PythonBoolean;
    forced: PythonBoolean;
    hi: PythonBoolean;
    language: CodeType;
  }

  interface Profile {
    name: string;
    profileId: number;
    cutoff: number | null;
    items: ProfileItem[];
  }
}

interface Subtitle {
  code2: Language.CodeType;
  name: string;
  forced: boolean;
  hi: boolean;
  path: string | null;
}

interface PathType {
  path: string;
}

interface SubtitlePathType {
  subtitles_path: string;
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
  audio_language: Language.Info[];
}

interface ItemHistoryType {
  language: Language.Info;
  provider: string;
}

declare namespace Item {
  type Base = PathType &
    TitleType &
    TagType &
    AudioLanguageType & {
      profileId: number | null;
      fanart: string;
      overview: string;
      imdbId: string;
      alternativeTitles: string[];
      poster: string;
      year: string;
    };

  type Series = Base &
    SeriesIdType & {
      hearing_impaired: boolean;
      episodeFileCount: number;
      episodeMissingCount: number;
      seriesType: SonarrSeriesType;
      tvdbId: number;
    };

  type Movie = Base &
    MovieIdType &
    MonitoredType &
    SubtitleType &
    MissingSubtitleType &
    SceneNameType & {
      hearing_impaired: boolean;
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
}

declare namespace Wanted {
  type Base = MonitoredType &
    TagType &
    SceneNameType & {
      // failedAttempts?: any;
      hearing_impaired: boolean;
      missing_subtitles: Subtitle[];
    };

  type Episode = Base &
    EpisodeIdType &
    EpisodeTitleType & {
      episode_number: string;
      seriesType: SonarrSeriesType;
    };

  type Movie = Base & MovieIdType & TitleType;
}

declare namespace Blacklist {
  type Base = ItemHistoryType & {
    parsed_timestamp: string;
    timestamp: string;
    subs_id: string;
  };

  type Movie = Base & MovieIdType & TitleType;

  type Episode = Base &
    EpisodeTitleType &
    SeriesIdType & {
      episode_number: string;
    };
}

declare namespace History {
  type Base = SubtitlePathType &
    TagType &
    MonitoredType &
    Partial<ItemHistoryType> & {
      action: number;
      blacklisted: boolean;
      score?: string;
      subs_id?: string;
      raw_timestamp: number;
      parsed_timestamp: string;
      timestamp: string;
      description: string;
      upgradable: boolean;
    };

  type Movie = History.Base & MovieIdType & TitleType;

  type Episode = History.Base &
    EpisodeIdType &
    EpisodeTitleType & {
      episode_number: string;
    };

  type StatItem = {
    count: number;
    date: string;
  };

  type Stat = {
    movies: StatItem[];
    series: StatItem[];
  };

  type TimeframeOptions = "week" | "month" | "trimester" | "year";
  type ActionOptions = 1 | 2 | 3;
}

declare namespace Parameter {
  interface Range {
    start: number;
    length: number;
  }
}

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

type ItemSearchResult = Partial<SeriesIdType> &
  Partial<MovieIdType> & {
    title: string;
    year: string;
  };
