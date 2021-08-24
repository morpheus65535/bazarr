import React, { useMemo } from "react";
import { Selector, SelectorProps } from "../components";

interface Props {
  options: readonly Language.Info[];
}

type RemovedSelectorProps<M extends boolean> = Omit<
  SelectorProps<Language.Info, M>,
  "label"
>;

export type LanguageSelectorProps<M extends boolean> = Override<
  Props,
  RemovedSelectorProps<M>
>;

function getLabel(lang: Language.Info) {
  return lang.name;
}

export function LanguageSelector<M extends boolean = false>(
  props: LanguageSelectorProps<M>
) {
  const { options, ...selector } = props;

  const items = useMemo<SelectorOption<Language.Info>[]>(
    () =>
      options.map((v) => ({
        label: v.name,
        value: v,
      })),
    [options]
  );

  return (
    <Selector
      placeholder="Language..."
      options={items}
      label={getLabel}
      {...selector}
    ></Selector>
  );
}
