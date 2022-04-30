import { useLanguages } from "@/apis/hooks";
import { Selector, SelectorOption, SelectorProps } from "@/components";
import { FunctionComponent, useMemo } from "react";

interface TextProps {
  value: Language.Info;
  className?: string;
  long?: boolean;
}

declare type LanguageComponent = {
  Text: typeof LanguageText;
  Selector: typeof LanguageSelector;
};

const LanguageText: FunctionComponent<TextProps> = ({
  value,
  className,
  long,
}) => {
  const result = useMemo(() => {
    let lang = value.code2;
    let hi = ":HI";
    let forced = ":Forced";
    if (long) {
      lang = value.name;
      hi = " HI";
      forced = " Forced";
    }

    let res = lang;
    if (value.hi) {
      res += hi;
    } else if (value.forced) {
      res += forced;
    }
    return res;
  }, [value, long]);

  return (
    <span title={value.name} className={className}>
      {result}
    </span>
  );
};

type LanguageSelectorProps<M extends boolean> = Omit<
  SelectorProps<Language.Info, M>,
  "label" | "options"
> & {
  history?: boolean;
};

function getLabel(lang: Language.Info) {
  return lang.name;
}

export function LanguageSelector<M extends boolean = false>(
  props: LanguageSelectorProps<M>
) {
  const { history, ...rest } = props;
  const { data: options } = useLanguages(history);

  const items = useMemo<SelectorOption<Language.Info>[]>(
    () =>
      options?.map((v) => ({
        label: v.name,
        value: v,
      })) ?? [],
    [options]
  );

  return (
    <Selector
      placeholder="Language..."
      options={items}
      label={getLabel}
      {...rest}
    ></Selector>
  );
}

const Components: LanguageComponent = {
  Text: LanguageText,
  Selector: LanguageSelector,
};

export default Components;
