import React, { FunctionComponent } from "react";
import { Button, ButtonProps } from "react-bootstrap";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";

interface CHButtonProps {
  iconProps: FontAwesomeIconProps;
  btnProps?: ButtonProps;
}

const ContentHeaderButton: FunctionComponent<CHButtonProps> = (props) => {
  const { children, iconProps, btnProps } = props;

  return (
    <Button variant="dark" className="d-flex flex-column" {...btnProps}>
      <FontAwesomeIcon
        size="lg"
        className="mx-auto"
        {...iconProps}
      ></FontAwesomeIcon>
      <span className="align-bottom text-themecolor small text-center">
        {children}
      </span>
    </Button>
  );
};

export default ContentHeaderButton;
