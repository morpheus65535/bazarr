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

namespace Profile {
  interface Item {
    id: number;
    audio_exclude: PythonBoolean;
    forced: PythonBoolean;
    hi: PythonBoolean;
    language: LanguageCodeType;
  }
  interface Languages {
    name: string;
    profileId: number;
    cutoff: number | null;
    items: Item[];
  }
}

interface Subtitle extends Language {
  forced: boolean;
  hi: boolean;
  path: string | null;
}

interface PathType {
  path: string;
  exist: boolean;
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
  audio_language: Language[];
}

interface ItemHistoryType {
  language: Language;
  provider: string;
}

namespace Item {
  type Base = PathType &
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

namespace Wanted {
  type Base = MonitoredType &
    PathType &
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
}

namespace Blacklist {
  type Base = ItemHistoryType & {
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

namespace History {
  type Base = PathType &
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

  type Movie = History.Base & MovieIdType & TitleType;

  type Episode = History.Base &
    EpisodeIdType &
    EpisodeTitleType & {
      episode_number: string;
    };
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
