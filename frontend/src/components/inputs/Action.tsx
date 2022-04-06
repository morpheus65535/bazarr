import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";
import { ActionIcon, ActionIconProps } from "@mantine/core";
import { FunctionComponent } from "react";

export type ActionProps = ActionIconProps<"button"> & {
  icon: IconDefinition;
  iconProps?: Omit<FontAwesomeIconProps, "icon">;
};

const Action: FunctionComponent<ActionProps> = ({
  icon,
  iconProps,
  ...props
}) => {
  return (
    <ActionIcon {...props}>
      <FontAwesomeIcon icon={icon} {...iconProps}></FontAwesomeIcon>
    </ActionIcon>
  );
};

export default Action;
