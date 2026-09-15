import { FunctionComponent, PropsWithChildren } from "react";
import { Collapse, Stack } from "@mantine/core";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";

interface ContentProps {
  settingKey: string;
  on?: (k: unknown) => boolean;
  indent?: boolean;
}

type Props = PropsWithChildren<ContentProps>;

const CollapseBox: FunctionComponent<Props> = ({
  on,
  indent,
  children,
  settingKey,
}) => {
  const value = useSettingValue(settingKey);

  const open = on ? on(value) : Boolean(value);

  return (
    <Collapse
      expanded={open}
      pl={indent ? "md" : undefined}
      transitionDuration={0}
    >
      <Stack gap="xs">{children}</Stack>
    </Collapse>
  );
};

export default CollapseBox;
