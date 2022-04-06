import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";
import { ActionIcon, ActionIconProps } from "@mantine/core";
import { forwardRef } from "react";

export type ActionProps = ActionIconProps<"button"> & {
  icon: IconDefinition;
  iconProps?: Omit<FontAwesomeIconProps, "icon">;
};

const Action = forwardRef<HTMLButtonElement, ActionProps>(
  ({ icon, iconProps, ...props }, ref) => {
    return (
      <ActionIcon {...props} ref={ref}>
        <FontAwesomeIcon icon={icon} {...iconProps}></FontAwesomeIcon>
      </ActionIcon>
    );
  }
);

export default Action;
