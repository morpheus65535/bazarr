import React, { useMemo } from "react";
import { Selector, SelectorProps } from "../components";

interface Props {
  options: readonly Language[];
}

type RemovedSelectorProps<M extends boolean> = Omit<
  SelectorProps<Language, M>,
  "label" | "placeholder"
>;

export type LanguageSelectorProps<M extends boolean> = Override<
  Props,
  RemovedSelectorProps<M>
>;

function getLabel(lang: Language) {
  return lang.name;
}

export function LanguageSelector<M extends boolean = false>(
  props: LanguageSelectorProps<M>
) {
  const { options, ...selector } = props;

  const items = useMemo<SelectorOption<Language>[]>(
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
