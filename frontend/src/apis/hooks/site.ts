import { useSystemSettings } from ".";

export const useEnabledStatus = () => {
  const { data } = useSystemSettings();

  return {
    sonarr: data?.general.use_sonarr ?? false,
    radarr: data?.general.use_radarr ?? false,
  };
};

export const useShowOnlyDesired = () => {
  const { data } = useSystemSettings();
  return data?.general.embedded_subs_show_desired ?? false;
};

export const useInstanceName = () => {
  const { data } = useSystemSettings();
  return data?.general.instance_name;
};
