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
      defaultValue={enabled}
      options={options}
      onChange={(val) => {
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

  const profileOptions = useMemo<SelectorOption<number>[]>(
    () =>
      profiles.map((v) => {
        return { label: v.name, value: v.profileId };
      }),
    [profiles]
  );

  return (
    <Selector
      clearable
      options={profileOptions}
      settingKey={settingKey}
      beforeStaged={(v) => (v === undefined ? "" : v)}
    ></Selector>
  );
};
