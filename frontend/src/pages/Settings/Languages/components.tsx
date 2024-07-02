import { FunctionComponent, useMemo } from "react";
import { Input } from "@mantine/core";
import {
  MultiSelector,
  MultiSelectorProps,
  SelectorOption,
} from "@/components";
import { Selector, SelectorProps } from "@/pages/Settings/components";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";
import { BaseInput } from "@/pages/Settings/utilities/hooks";
import { useSelectorOptions } from "@/utilities";
import { useLatestEnabledLanguages, useLatestProfiles } from ".";

type LanguageSelectorProps = Omit<
  MultiSelectorProps<Language.Info>,
  "options" | "value" | "onChange"
> & {
  options: readonly Language.Info[];
};

export const LanguageSelector: FunctionComponent<
  LanguageSelectorProps & BaseInput<string[]>
> = ({ settingKey, label, options }) => {
  const enabled = useLatestEnabledLanguages();
  const { setValue } = useFormActions();

  const wrappedOptions = useSelectorOptions(options, (value) => value.name);

  return (
    <Input.Wrapper label={label}>
      <MultiSelector
        {...wrappedOptions}
        value={enabled}
        searchable
        onChange={(val) => {
          setValue(val, settingKey, (value: Language.Info[]) =>
            value.map((v) => v.code2),
          );
        }}
      ></MultiSelector>
    </Input.Wrapper>
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
    [profiles],
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
