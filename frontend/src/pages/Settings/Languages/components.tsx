import {
  MultiSelector,
  MultiSelectorProps,
  SelectorOption,
} from "@/components";
import { Language } from "@/components/bazarr";
import { useSelectorOptions } from "@/utilities";
import { FunctionComponent, useMemo } from "react";
import { useLatestEnabledLanguages, useLatestProfiles } from ".";
import { BaseInput, Selector, SelectorProps } from "../components";
import { useFormActions } from "../utilities/FormValues";

type LanguageSelectorProps = Omit<
  MultiSelectorProps<Language.Info>,
  "options" | "value" | "onChange"
> & {
  options: readonly Language.Info[];
};

export const LanguageSelector: FunctionComponent<
  LanguageSelectorProps & BaseInput<string[]>
> = ({ settingKey, options }) => {
  const enabled = useLatestEnabledLanguages();
  const { setValue } = useFormActions();

  const wrappedOptions = useSelectorOptions(options, (value) => value.name);

  return (
    <MultiSelector
      {...wrappedOptions}
      value={enabled}
      searchable
      onChange={(val) => {
        setValue(val, settingKey);
      }}
    ></MultiSelector>
  );
};

export const ProfileSelector: FunctionComponent<
  Omit<SelectorProps<number>, "beforeStaged" | "options" | "clearable">
> = ({ ...props }) => {
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
      {...props}
      clearable
      options={profileOptions}
      beforeStaged={(v) => (v === null ? "" : v)}
    ></Selector>
  );
};
