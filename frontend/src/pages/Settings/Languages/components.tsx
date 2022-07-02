import {
  MultiSelector,
  MultiSelectorProps,
  SelectorOption,
} from "@/components";
import { Language } from "@/components/bazarr";
import { useSelectorOptions } from "@/utilities";
import { InputWrapper } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { useLatestEnabledLanguages, useLatestProfiles } from ".";
import { Selector, SelectorProps } from "../components";
import { useFormActions } from "../utilities/FormValues";
import { BaseInput } from "../utilities/hooks";

type LanguageSelectorProps = Omit<
  MultiSelectorProps<Language.Info>,
  "options" | "value" | "onChange"
> & {
  options: readonly Language.Info[];
};

export const LanguageSelector: FunctionComponent<
  LanguageSelectorProps & BaseInput<string[]>
> = ({ settingKey, location, label, options }) => {
  const enabled = useLatestEnabledLanguages();
  const { setValue } = useFormActions();

  const wrappedOptions = useSelectorOptions(options, (value) => value.name);

  return (
    <InputWrapper label={label}>
      <MultiSelector
        {...wrappedOptions}
        value={enabled}
        searchable
        onChange={(val) => {
          setValue(val, settingKey, location);
        }}
      ></MultiSelector>
    </InputWrapper>
  );
};

export const ProfileSelector: FunctionComponent<
  Omit<SelectorProps<number>, "settingOptions" | "options" | "clearable">
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
      settingOptions={{ onSubmit: (v) => (v === null ? "" : v) }}
    ></Selector>
  );
};
