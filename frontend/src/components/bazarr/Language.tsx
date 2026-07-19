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
    const lang = long ? value.name : value.code2;
    const hi = long ? " HI" : ":HI";
    const forced = long ? " Forced" : ":Forced";
    const res = lang + (value.hi ? hi : value.forced ? forced : "");
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
