import { LanguageSelector as CLanguageSelector } from "components";
import React, { FunctionComponent, useMemo } from "react";
import { useEnabledLanguagesContext, useProfilesContext } from ".";
import { BaseInput, Selector, useSingleUpdate } from "../components";

interface LanguageSelectorProps {
  options: readonly Language.Info[];
}

export const LanguageSelector: FunctionComponent<
  LanguageSelectorProps & BaseInput<string[]>
> = ({ settingKey, options }) => {
  const enabled = useEnabledLanguagesContext();
  const update = useSingleUpdate();

  return (
    <CLanguageSelector
      multiple
      value={enabled}
      options={options}
      onChange={(val) => {
        update(val, settingKey);
      }}
    ></CLanguageSelector>
  );
};

interface ProfileSelectorProps {}

export const ProfileSelector: FunctionComponent<
  ProfileSelectorProps & BaseInput<Language.Profile>
> = ({ settingKey }) => {
  const profiles = useProfilesContext();

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
      beforeStaged={(v) => (v === null ? "" : v)}
    ></Selector>
  );
};
