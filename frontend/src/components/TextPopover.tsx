import { FunctionComponent, ReactElement } from "react";
import { Tooltip, TooltipProps } from "@mantine/core";
import { useHover } from "@mantine/hooks";
import { isNull, isUndefined } from "lodash";

interface TextPopoverProps {
  children: ReactElement;
  text: string | undefined | null;
  tooltip?: Omit<TooltipProps, "opened" | "label" | "children">;
}

const TextPopover: FunctionComponent<TextPopoverProps> = ({
  children,
  text,
  tooltip,
}) => {
  const { hovered, ref } = useHover();

  if (isNull(text) || isUndefined(text)) {
    return children;
  }

  return (
    <Tooltip opened={hovered} label={text} {...tooltip}>
      <div ref={ref}>{children}</div>
    </Tooltip>
  );
};

export default TextPopover;
