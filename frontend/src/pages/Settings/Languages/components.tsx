import { MultiSelector, SelectorOption } from "@/components";
import { Language } from "@/components/bazarr";
import { useSelectorOptions } from "@/utilities";
import { FunctionComponent, useMemo } from "react";
import { useLatestEnabledLanguages, useLatestProfiles } from ".";
import { BaseInput, Selector, useSingleUpdate } from "../components";

interface LanguageSelectorProps {
  options: readonly Language.Info[];
}

export const LanguageSelector: FunctionComponent<
  LanguageSelectorProps & BaseInput<string[]>
> = ({ settingKey, options }) => {
  const enabled = useLatestEnabledLanguages();
  const update = useSingleUpdate();

  const wrappedOptions = useSelectorOptions(options, (value) => value.name);

  return (
    <MultiSelector
      {...wrappedOptions}
      value={enabled}
      searchable
      getLabel={(v: Language.Info) => v.name}
      onChange={(val) => {
        update(val, settingKey);
      }}
    ></MultiSelector>
  );
};

export const ProfileSelector: FunctionComponent<
  BaseInput<Language.Profile>
> = ({ settingKey }) => {
  const profiles = useLatestProfiles();

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
