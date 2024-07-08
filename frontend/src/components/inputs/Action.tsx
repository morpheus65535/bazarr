import { forwardRef } from "react";
import {
  ActionIcon,
  ActionIconProps,
  Tooltip,
  TooltipProps,
} from "@mantine/core";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";

export type ActionProps = MantineComp<ActionIconProps, "button"> & {
  icon: IconDefinition;
  label: string;
  tooltip?: Omit<TooltipProps, "label" | "children">;
  iconProps?: Omit<FontAwesomeIconProps, "icon">;
};

const Action = forwardRef<HTMLButtonElement, ActionProps>(
  ({ icon, iconProps, label, tooltip, ...props }, ref) => {
    return (
      <Tooltip openDelay={1500} {...tooltip} label={label}>
        <ActionIcon aria-label={label} {...props} ref={ref}>
          <FontAwesomeIcon icon={icon} {...iconProps}></FontAwesomeIcon>
        </ActionIcon>
      </Tooltip>
    );
  },
);

export default Action;
