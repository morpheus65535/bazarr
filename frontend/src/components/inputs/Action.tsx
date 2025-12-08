import { forwardRef } from "react";
import {
  ActionIcon,
  ActionIconProps,
  Loader,
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
  isLoading?: boolean;
};

const Action = forwardRef<HTMLButtonElement, ActionProps>(
  ({ icon, iconProps, label, tooltip, isLoading, size, ...props }, ref) => {
    return (
      <Tooltip openDelay={1500} {...tooltip} label={label}>
        <ActionIcon aria-label={label} {...props} ref={ref}>
          {isLoading ? (
            <Loader size={size} />
          ) : (
            <FontAwesomeIcon icon={icon} {...iconProps}></FontAwesomeIcon>
          )}
        </ActionIcon>
      </Tooltip>
    );
  },
);

export default Action;
