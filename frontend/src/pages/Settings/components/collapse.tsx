import { Collapse } from "@mantine/core";
import { FunctionComponent, useMemo, useRef } from "react";
import { useSettingValue } from "./hooks";

interface ContentProps {
  settingKey: string;
  on?: (k: unknown) => boolean;
  indent?: boolean;
}

const CollapseBox: FunctionComponent<ContentProps> = ({
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
      <div>{children}</div>
    </Collapse>
  );
};

export default CollapseBox;
