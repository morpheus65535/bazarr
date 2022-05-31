import { useSystemSettings } from ".";

export function useEnabledStatus() {
  const { data } = useSystemSettings();

  return {
    sonarr: data?.general.use_sonarr ?? false,
    radarr: data?.general.use_radarr ?? false,
  };
}

export function useShowOnlyDesired() {
  const { data } = useSystemSettings();
  return data?.general.embedded_subs_show_desired ?? false;
}
