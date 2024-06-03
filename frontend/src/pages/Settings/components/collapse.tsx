import { Collapse, Stack } from "@mantine/core";
import { FunctionComponent, PropsWithChildren, useMemo, useRef } from "react";
import { useSettingValue } from "../utilities/hooks";

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

  const onRef = useRef(on);
  onRef.current = on;

  const open = useMemo<boolean>(() => {
    if (onRef.current) {
      return onRef.current(value);
    } else {
      return Boolean(value);
    }
  }, [value]);

  return (
    <Collapse in={open} pl={indent ? "md" : undefined}>
      <Stack gap="xs">{children}</Stack>
    </Collapse>
  );
};

export default CollapseBox;
