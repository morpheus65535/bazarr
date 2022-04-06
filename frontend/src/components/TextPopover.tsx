import { Tooltip } from "@mantine/core";
import { useHover } from "@mantine/hooks";
import { isNull, isUndefined } from "lodash";
import { FunctionComponent, ReactElement } from "react";

interface TextPopoverProps {
  children: ReactElement;
  text: string | undefined | null;
}

const TextPopover: FunctionComponent<TextPopoverProps> = ({
  children,
  text,
}) => {
  const { hovered, ref } = useHover();

  if (isNull(text) || isUndefined(text)) {
    return children;
  }

  return (
    <Tooltip opened={hovered} label={text}>
      <div ref={ref}>{children}</div>
    </Tooltip>
  );
};

export default TextPopover;
