import React, { FunctionComponent, MouseEvent } from "react";
import { Button, ButtonProps } from "react-bootstrap";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";

interface CHButtonProps {
  iconProps: FontAwesomeIconProps;
  btnProps?: ButtonProps;
  disabled?: boolean;
  onClick?: (e: MouseEvent) => void;
}

const ContentHeaderButton: FunctionComponent<CHButtonProps> = (props) => {
  const { children, iconProps, btnProps, disabled, onClick } = props;

  return (
    <Button
      variant="dark"
      className="d-flex flex-column"
      {...btnProps}
      disabled={disabled}
      onClick={onClick}
    >
      <FontAwesomeIcon
        size="lg"
        className="mx-auto my-1"
        {...iconProps}
      ></FontAwesomeIcon>
      <span className="align-bottom text-themecolor small text-center">
        {children}
      </span>
    </Button>
  );
};

export default ContentHeaderButton;
