import React, { useMemo } from "react";
import { Selector, SelectorProps } from "../components";

interface Props {
  options: readonly Language[];
}

type RemovedSelectorProps<M extends boolean> = Omit<
  SelectorProps<Language, M>,
  "label"
>;

function LanguageSelector<M extends boolean = false>(
  props: Override<Props, RemovedSelectorProps<M>>
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
    <Selector options={items} label={(l) => l.name} {...selector}></Selector>
  );
}

export default LanguageSelector;
