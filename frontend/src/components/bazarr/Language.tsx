import { FunctionComponent, useMemo } from "react";
import { Badge, Group, Text, TextProps } from "@mantine/core";
import { BuildKey } from "@/utilities";

type LanguageTextProps = TextProps & {
  value: Language.Info;
  long?: boolean;
};

declare type LanguageComponent = {
  Text: typeof LanguageText;
  List: typeof LanguageList;
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

type LanguageListProps = {
  value: Language.Info[];
};

const LanguageList: FunctionComponent<LanguageListProps> = ({ value }) => {
  return (
    <Group gap="xs">
      {value.map((v) => (
        <Badge key={BuildKey(v.code2, v.code2, v.hi)}>{v.name}</Badge>
      ))}
    </Group>
  );
};

const Components: LanguageComponent = {
  Text: LanguageText,
  List: LanguageList,
};

export default Components;
