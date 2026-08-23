interface Badge {
  episodes: number;
  movies: number;
  providers: number;
  status: number;
  sonarr_signalr: string;
  radarr_signalr: string;
  announcements: number;
}

declare namespace Language {
  type CodeType = string;
  interface Server {
    code2: CodeType;
    code3: CodeType;
    name: string;
    enabled: boolean;
  }

  interface Info {
    code2: CodeType;
    name: string;
    hi?: boolean;
    forced?: boolean;
  }

  interface RawProfileItem {
    id: number;
    audio_exclude: PythonBoolean;
    audio_only_include: PythonBoolean;
    forced: PythonBoolean;
    hi: HiPreference;
    language: CodeType;
  }

  type ProfileItem = CamelCaseKeys<RawProfileItem>;

  interface RawProfile {
    name: string;
    profileId: number;
    cutoff: number | null;
    items: RawProfileItem[];
    mustContain: string[];
    mustNotContain: string[];
    originalFormat: boolean | null;
    autoTranslate: boolean | null;
    tag: string | undefined;
  }

  type Profile = CamelCaseKeys<RawProfile>;
}

interface RawSubtitle {
  code2: Language.CodeType;
  name: string;
  forced: boolean;
  hi: boolean;
  path: string | null | undefined; // TODO: FIX ME!!!!!!
  embedded_track_id: number | null | undefined; // TODO: FIX ME!!!!!!
  id: number;
}

type Subtitle = CamelCaseKeys<RawSubtitle>;

interface AudioTrack {
  stream: string;
  name: string;
  language: string;
}

interface RawSubtitleTrack {
  stream: string;
  name: string;
  language: string;
  forced: boolean;
  hearing_impaired: boolean;
}

type SubtitleTrack = CamelCaseKeys<RawSubtitleTrack>;

interface RawExternalSubtitle {
  name: string;
  path: string;
  language: string;
  forced: boolean;
  hearing_impaired: boolean;
}

type ExternalSubtitle = CamelCaseKeys<RawExternalSubtitle>;

interface PathType {
  path: string;
}

interface SubtitlePathType {
  subtitles_path: string;
}

interface MonitoredType {
  monitored: boolean;
}

interface RawSubtitleType {
  subtitles: RawSubtitle[];
}

type SubtitleType = CamelCaseKeys<RawSubtitleType>;

interface RawMissingSubtitleType {
  missing_subtitles: RawSubtitle[];
}

type MissingSubtitleType = CamelCaseKeys<RawMissingSubtitleType>;

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

interface RawAudioLanguageType {
  audio_language: Language.Info[];
}

type AudioLanguageType = CamelCaseKeys<RawAudioLanguageType>;

interface ItemHistoryType {
  language: Language.Info;
  provider: string;
}

declare namespace Item {
  type RawBase = PathType &
    TitleType &
    TagType &
    MonitoredType &
    RawAudioLanguageType & {
      created_at_timestamp?: string | null;
      profileId: number | null;
      fanart: string;
      overview: string;
      imdbId: string;
      alternativeTitles: string[];
      poster: string;
      year: string;
    };

  type Base = CamelCaseKeys<RawBase>;

  type RawSeries = RawBase &
    SeriesIdType & {
      episodeFileCount: number;
      episodeMissingCount: number;
      ended: boolean;
      lastAired: string;
      seriesType: SonarrSeriesType;
      tvdbId: number;
    };

  type Series = CamelCaseKeys<RawSeries>;

  type RawMovie = RawBase &
    MovieIdType &
    RawSubtitleType &
    RawMissingSubtitleType &
    SceneNameType;

  type Movie = CamelCaseKeys<RawMovie>;

  type RawEpisode = PathType &
    TitleType &
    MonitoredType &
    EpisodeIdType &
    RawSubtitleType &
    RawMissingSubtitleType &
    SceneNameType &
    RawAudioLanguageType & {
      season: number;
      episode: number;
    };

  type Episode = CamelCaseKeys<RawEpisode>;

  interface RawRefTracks {
    audio_tracks: AudioTrack[];
    embedded_subtitles_tracks: RawSubtitleTrack[];
    external_subtitles_tracks: RawExternalSubtitle[];
  }

  type RefTracks = CamelCaseKeys<RawRefTracks>;
}

declare namespace Wanted {
  type RawBase = MonitoredType &
    TagType &
    SceneNameType & {
      hearing_impaired: boolean;
      missing_subtitles: RawSubtitle[];
    };

  type Base = CamelCaseKeys<RawBase>;

  type RawEpisode = RawBase &
    EpisodeIdType &
    EpisodeTitleType & {
      episode_number: string;
      seriesType: SonarrSeriesType;
    };

  type Episode = CamelCaseKeys<RawEpisode>;

  type RawMovie = RawBase & MovieIdType & TitleType;

  type Movie = CamelCaseKeys<RawMovie>;
}

declare namespace Blacklist {
  type RawBase = ItemHistoryType & {
    parsed_timestamp: string;
    timestamp: string;
    subs_id: string;
  };

  type RawMovie = RawBase & MovieIdType & TitleType;

  type RawEpisode = RawBase &
    EpisodeTitleType &
    SeriesIdType & {
      episode_number: string;
    };

  type Base = CamelCaseKeys<RawBase>;
  type Movie = CamelCaseKeys<RawMovie>;
  type Episode = CamelCaseKeys<RawEpisode>;
}

declare namespace History {
  type RawBase = SubtitlePathType &
    TagType &
    MonitoredType &
    Partial<ItemHistoryType> & {
      action: number;
      blacklisted: boolean;
      score?: string;
      subs_id?: string;
      parsed_timestamp: string;
      timestamp: string;
      description: string;
      upgradable: boolean;
      matches: string[];
      dont_matches: string[];
    };

  type RawMovie = RawBase & MovieIdType & TitleType;

  type RawEpisode = RawBase &
    EpisodeIdType &
    EpisodeTitleType & {
      episode_number: string;
    };

  type Base = CamelCaseKeys<RawBase>;
  type Movie = CamelCaseKeys<RawMovie>;
  type Episode = CamelCaseKeys<RawEpisode>;

  type StatItem = {
    count: number;
    date: string;
  };

  type Stat = {
    movies: StatItem[];
    series: StatItem[];
  };

  type TimeFrameOptions = "week" | "month" | "trimester" | "year";
  type ActionOptions = 1 | 2 | 3;
}

declare namespace Parameter {
  interface Range {
    start: number;
    length: number;
  }

  interface ListFilters {
    monitored?: boolean;
    missing?: boolean;
    profileId?: number;
    audioLanguage?: string;
    tags?: string[];
  }

  interface ListQuery extends Range {
    sortBy?: string;
    sortOrder?: "asc" | "desc";
    filters?: ListFilters;
  }

  // ListQuery without the paging fields, as managed by the filter/sort UI
  // state (URL params) and passed to the pagination hooks.
  type ListState = Omit<ListQuery, "start" | "length">;
}

declare namespace Plex {
  interface Pin {
    pinId: string;
    code: string;
    clientId: string;
    authUrl: string;
  }

  interface RawValidationResult {
    valid: boolean;
    auth_method?: string;
    username?: string;
    email?: string;
    error?: string;
    code?: string;
  }

  type ValidationResult = CamelCaseKeys<RawValidationResult>;

  interface PinCheckResult {
    authenticated: boolean;
    username?: string;
    email?: string;
    error?: string;
  }

  interface ServerConnection {
    uri: string;
    protocol: string;
    address: string;
    port: number;
    local: boolean;
    available?: boolean;
    latency?: number;
  }

  interface Server {
    name: string;
    machineIdentifier: string;
    connections: ServerConnection[];
    version: string;
    platform: string;
    device: string;
    bestConnection?: ServerConnection | null;
  }

  interface Library {
    key: string;
    title: string;
    type: string;
    count: number;
    agent: string;
    scanner: string;
    language: string;
    uuid: string;
    updatedAt: number;
    createdAt: number;
    locations: string[];
  }

  interface RawWebhookResult {
    success: boolean;
    message: string;
    webhook_url?: string;
    total_webhooks?: number;
  }

  type WebhookResult = CamelCaseKeys<RawWebhookResult>;

  interface WebhookInfo {
    url: string;
  }

  interface RawPlexPassSubscription {
    active: boolean;
    has_webhooks_feature: boolean;
    plan: string | null;
  }

  type PlexPassSubscription = CamelCaseKeys<RawPlexPassSubscription>;

  interface RawWebhookList {
    webhooks: WebhookInfo[];
    count: number;
    plexPassSubscription?: RawPlexPassSubscription;
  }

  type WebhookList = CamelCaseKeys<RawWebhookList>;

  interface AutopulseResult {
    success: boolean;
    message: string;
  }

  interface RawAutopulseConfig {
    config_yaml: string;
    server_name: string;
    rewrite_detected?: boolean;
    rewrite_suggestion?: string;
    template_info?: string;
  }

  type AutopulseConfig = CamelCaseKeys<RawAutopulseConfig>;

  interface AutopulseLibrary {
    key: string;
    title: string;
    type: string;
    locations: string[];
  }
}

interface RawSearchResultType {
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
  subtitle: unknown;
  uploader?: string;
  url?: string;
  original_format: PythonBoolean;
}

type SearchResultType = CamelCaseKeys<RawSearchResultType>;

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

declare namespace SubtitleContents {
  interface RawLineTime {
    hours: number;
    minutes: number;
    seconds: number;
    total_seconds: number;
    microseconds: number;
  }

  type LineTime = CamelCaseKeys<RawLineTime>;

  interface RawLine {
    index: number;
    content: string;
    proprietary: string;
    start: RawLineTime;
    end: RawLineTime;
    // duration: LineTime;
  }

  type Line = CamelCaseKeys<RawLine>;

  // interface Contents extends Array<Line> {}
}

type ItemSearchResult = Partial<SeriesIdType> &
  Partial<MovieIdType> & {
    title: string;
    year: string;
    poster: string;
  };

type BackendError = {
  code: number;
  message: string;
};
