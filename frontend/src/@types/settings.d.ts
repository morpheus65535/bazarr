interface SystemSettings {
  general: GeneralSettings;
  proxy: ProxySettings;
  auth: AuthSettings;
  subsync: SubsyncSettings;
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
  minimum_score: number;
  minimum_score_movie: number;
  movie_default_enabled: boolean;
  movie_default_forced: boolean;
  movie_default_hi: boolean;
  movie_default_language: string[];
  serie_default_enabled: boolean;
  serie_default_forced: boolean;
  serie_default_hi: boolean;
  serie_default_language: string[];
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
  subzero_mods: string[];
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
  type: string;
  url: string;
  port: number;
  username?: string;
}

interface AuthSettings {
  type?: string;
  username?: string;
}

interface SubsyncSettings {
  use_subsync: boolean;
  use_subsync_threshold: boolean;
  subsync_threshold: number;
  use_subsync_movie_threshold: boolean;
  subsync_movie_threshold: number;
  debug: boolean;
}

// Providers
