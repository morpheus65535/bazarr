interface Settings {
  general: Settings.General;
  proxy: Settings.Proxy;
  auth: Settings.Auth;
  subsync: Settings.Subsync;
  analytics: Settings.Analytic;
  sonarr: Settings.Sonarr;
  radarr: Settings.Radarr;
  // Anitcaptcha
  anticaptcha: Settings.Anticaptcha;
  deathbycaptcha: Settings.DeathByCaptche;
  // Providers
  opensubtitles: Settings.OpenSubtitles;
  opensubtitlescom: Settings.OpenSubtitlesCom;
  addic7ed: Settings.Addic7ed;
  legendasdivx: Settings.Legandasdivx;
  legendastv: Settings.Legendastv;
  xsubs: Settings.XSubs;
  assrt: Settings.Assrt;
  napisy24: Settings.Napisy24;
  subscene: Settings.Subscene;
  betaseries: Settings.Betaseries;
  titlovi: Settings.Titlovi;
  ktuvit: Settings.Ktuvit;
  notifications: Settings.Notifications;
}

declare namespace Settings {
  interface General {
    adaptive_searching: boolean;
    anti_captcha_provider?: string;
    auto_update: boolean;
    base_url?: string;
    branch: string;
    chmod?: string;
    chmod_enabled: boolean;
    days_to_upgrade_subs: number;
    debug: boolean;
    dont_notify_manual_actions: boolean;
    embedded_subs_show_desired: boolean;
    enabled_providers: string[];
    ignore_pgs_subs: boolean;
    ignore_vobsub_subs: boolean;
    ip: string;
    multithreading: boolean;
    minimum_score: number;
    minimum_score_movie: number;
    movie_default_enabled: boolean;
    movie_default_profile?: number;
    serie_default_enabled: boolean;
    serie_default_profile?: number;
    path_mappings: [string, string][];
    path_mappings_movie: [string, string][];
    port: number;
    upgrade_subs: boolean;
    postprocessing_cmd?: string;
    postprocessing_threshold: number;
    postprocessing_threshold_movie: number;
    single_language: boolean;
    subfolder: string;
    subfolder_custom?: string;
    subzero_mods?: string[];
    subzero_color_selection?: string;
    update_restart: boolean;
    upgrade_frequency: number;
    upgrade_manual: boolean;
    use_embedded_subs: boolean;
    use_postprocessing: boolean;
    use_postprocessing_threshold: boolean;
    use_postprocessing_threshold_movie: boolean;
    use_radarr: boolean;
    use_scenename: boolean;
    use_sonarr: boolean;
    utf8_encode: boolean;
    wanted_search_frequency: number;
    wanted_search_frequency_movie: number;
  }

  interface Proxy {
    exclude: string[];
    type?: string;
    url?: string;
    port?: number;
    username?: string;
    password?: string;
  }

  interface Auth {
    type?: string;
    username?: string;
    password?: string;
    apikey: string;
  }

  interface Subsync {
    use_subsync: boolean;
    use_subsync_threshold: boolean;
    subsync_threshold: number;
    use_subsync_movie_threshold: boolean;
    subsync_movie_threshold: number;
    debug: boolean;
  }

  interface Analytic {
    enabled: boolean;
  }

  interface Notifications {
    providers: NotificationInfo[];
  }

  interface NotificationInfo {
    enabled: boolean;
    name: string;
    url: string | null;
  }

  // Sonarr / Radarr
  type FullUpdateOptions = "Manually" | "Daily" | "Weekly";

  interface Sonarr {
    ip: string;
    port: number;
    base_url?: string;
    ssl: boolean;
    apikey?: string;
    full_update: FullUpdateOptions;
    full_update_day: number;
    full_update_hour: number;
    only_monitored: boolean;
    series_sync: number;
    episodes_sync: number;
    excluded_tags: string[];
    excluded_series_types: SonarrSeriesType[];
  }

  interface Radarr {
    ip: string;
    port: number;
    base_url?: string;
    ssl: boolean;
    apikey?: string;
    full_update: FullUpdateOptions;
    full_update_day: number;
    full_update_hour: number;
    only_monitored: boolean;
    movies_sync: number;
    excluded_tags: string[];
  }

  interface Anticaptcha {
    anti_captcha_key?: string;
  }

  interface DeathByCaptche {
    username?: string;
    password?: string;
  }

  // Providers

  interface BaseProvider {
    username?: string;
    password?: string;
  }

  interface OpenSubtitles extends BaseProvider {
    use_tag_search: boolean;
    vip: boolean;
    ssl: boolean;
    timeout: number;
    skip_wrong_fps: boolean;
  }

  interface OpenSubtitlesCom extends BaseProvider {
    use_hash: boolean;
  }

  interface Addic7ed extends BaseProvider {}

  interface Legandasdivx extends BaseProvider {
    skip_wrong_fps: boolean;
  }

  interface Legendastv extends BaseProvider {
    featured_only: boolean;
  }

  interface XSubs extends BaseProvider {}

  interface Napisy24 extends BaseProvider {}

  interface Subscene extends BaseProvider {}

  interface Titlovi extends BaseProvider {}

  interface Ktuvit {
    email?: string;
    hashed_password?: string;
  }

  interface Betaseries {
    token?: string;
  }

  interface Assrt {
    token?: string;
  }
}
