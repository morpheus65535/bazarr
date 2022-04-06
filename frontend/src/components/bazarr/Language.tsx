import { Text, TextProps } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";

type LanguageTextProps = TextProps<"div"> & {
  value: Language.Info;
  long?: boolean;
};

declare type LanguageComponent = {
  Text: typeof LanguageText;
};

const LanguageText: FunctionComponent<LanguageTextProps> = ({
  value,
  long,
  ...props
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
    <Text inherit {...props}>
      {result}
    </Text>
  );
};

const Components: LanguageComponent = {
  Text: LanguageText,
};

export default Components;
