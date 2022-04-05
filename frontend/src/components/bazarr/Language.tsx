import { FunctionComponent, useMemo } from "react";

interface TextProps {
  value: Language.Info;
  className?: string;
  long?: boolean;
}

declare type LanguageComponent = {
  Text: typeof LanguageText;
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

const Components: LanguageComponent = {
  Text: LanguageText,
};

export default Components;
