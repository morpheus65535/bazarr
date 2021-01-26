import React, { FunctionComponent, useMemo } from "react";
import { useEnabledLanguages, useLanguagesProfile } from ".";
import { LanguageSelector as CLanguageSelector } from "../../components";

import { BasicInput, Selector, useUpdate } from "../components";

interface LanguageSelectorProps {
  options: Language[];
}

export const LanguageSelector: FunctionComponent<
  LanguageSelectorProps & BasicInput<string[]>
> = ({ settingKey, options }) => {
  const enabled = useEnabledLanguages();
  const update = useUpdate();
  return (
    <CLanguageSelector
      multiple
      defaultSelect={enabled}
      options={options}
      onChange={(val: Language[]) => {
        update(val, settingKey);
      }}
    ></CLanguageSelector>
  );
};

interface ProfileSelectorProps {}

export const ProfileSelector: FunctionComponent<
  ProfileSelectorProps & BasicInput<LanguagesProfile>
> = ({ settingKey }) => {
  const profiles = useLanguagesProfile();

  const profileOptions = useMemo<Pair[]>(
    () =>
      profiles.map<Pair>((v) => {
        return { key: v.profileId.toString(), value: v.name };
      }),
    [profiles]
  );

  return (
    <Selector
      options={profileOptions}
      nullKey="None"
      settingKey={settingKey}
      preprocess={(v: string) => (v === "None" ? "" : v)}
    ></Selector>
  );
};
