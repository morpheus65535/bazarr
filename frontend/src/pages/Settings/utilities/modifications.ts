export const BaseUrlModification = (settings: Settings) =>
  settings.general.base_url?.slice(1) ?? "";

export const SubzeroModification = (key: string) => (settings: Settings) =>
  settings.general.subzero_mods?.includes(key) ?? false;

export const SubzeroColorModification = (settings: Settings) =>
  settings.general.subzero_mods?.find((v) => v.startsWith("color")) ?? "";
