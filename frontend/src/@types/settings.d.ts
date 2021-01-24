interface SystemSettings {
  general: GeneralSettings;
  proxy: ProxySettings;
  auth: AuthSettings;
  subsync: SubsyncSettings;
  analytics: AnalyticSettings;
  sonarr: SonarrSettings;
  radarr: RadarrSettings;
  // Anitcaptcha
  anticaptcha: AnticaptchaSettings;
  deathbycaptcha: DeathByCaptcheSettings;
  // Providers
  opensubtitles: OpenSubtitlesSettings;
  addic7ed: Addic7edSettings;
  legendasdivx: LegandasdivxSettings;
  legendastv: LegendastvSettings;
  xsubs: XSubsSettings;
  assrt: AssrtSettings;
  napisy24: Napisy24Settings;
  subscene: SubsceneSettings;
  betaseries: BetaseriesSettings;
  titlovi: titloviSettings;
}

// Basic

interface GeneralSettings {
  adaptive_searching: boolean;
  anti_captcha_provider?: string;
  auto_update: boolean;
  base_url?: string;
  branch: string;
  chmod: number;
  chmod_enabled: boolean;
  days_to_upgrade_subs: number;
  debug: boolean;
  dont_notify_manual_actions: boolean;
  embeddeenabled_providersd_subs_show_desired: boolean;
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
  path_mappings: string[];
  path_mappings_movie: string[];
  port: number;
  upgrade_subs: boolean;
  postprocessing_cmd?: string;
  postprocessing_threshold: number;
  postprocessing_threshold_movie: number;
  single_language: boolean;
  subfolder: string;
  subfolder_custom?: string;
  subzero_mods?: string[];
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

interface ProxySettings {
  exclude: string[];
  type?: string;
  url?: string;
  port?: number;
  username?: string;
  password?: string;
}

interface AuthSettings {
  type?: string;
  username?: string;
  password?: string;
  apikey: string;
}

interface SubsyncSettings {
  use_subsync: boolean;
  use_subsync_threshold: boolean;
  subsync_threshold: number;
  use_subsync_movie_threshold: boolean;
  subsync_movie_threshold: number;
  debug: boolean;
}

interface AnalyticSettings {
  enabled: boolean;
}

// Sonarr / Radarr
type FullUpdateOptions = "Manually" | "Daily" | "Weekly";

interface SonarrSettings {
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

interface RadarrSettings {
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

interface AnticaptchaSettings {
  anti_captcha_key?: string;
}

interface DeathByCaptcheSettings {
  username?: string;
  password?: string;
}

// Providers

interface BasicProviderSettings {
  username?: string;
  password?: string;
}

interface OpenSubtitlesSettings extends BasicProviderSettings {
  use_tag_search: boolean;
  vip: boolean;
  ssl: boolean;
  timeout: number;
  skip_wrong_fps: boolean;
}

interface Addic7edSettings extends BasicProviderSettings {}

interface LegandasdivxSettings extends BasicProviderSettings {
  skip_wrong_fps: boolean;
}

interface LegendastvSettings extends BasicProviderSettings {}

interface XSubsSettings extends BasicProviderSettings {}

interface Napisy24Settings extends BasicProviderSettings {}

interface SubsceneSettings extends BasicProviderSettings {}

interface titloviSettings extends BasicProviderSettings {}

interface BetaseriesSettings {
  token?: string;
}

interface AssrtSettings {
  token?: string;
}
