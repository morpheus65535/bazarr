import { FunctionComponent, ReactElement } from "react";
import { Tooltip, TooltipProps } from "@mantine/core";
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
  if (isNull(text) || isUndefined(text)) {
    return children;
  }

  return (
    <Tooltip
      label={text}
      {...tooltip}
      style={{ textWrap: "wrap" }}
      events={{ hover: true, focus: false, touch: true }}
    >
      <div>{children}</div>
    </Tooltip>
  );
};

export default TextPopover;
