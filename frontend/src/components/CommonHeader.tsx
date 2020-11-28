import React, { FunctionComponent } from "react";
import { Navbar, Nav, Button, ButtonProps } from "react-bootstrap";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";

interface BtnProps {
  iconProps: FontAwesomeIconProps;
  btnProps?: ButtonProps;
}

export const CommonHeaderBtn: FunctionComponent<BtnProps> = (props) => {
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

type GroupDir = "start" | "end";
interface GroupProps {
  dir: GroupDir;
}

export const CommonHeaderGroup: FunctionComponent<GroupProps> = (props) => {
  const { children, dir } = props;

  const className = `d-flex flex-grow-1 justify-content-${dir}`;
  return <div className={className}>{children}</div>;
};

export const CommonHeader: FunctionComponent = (props) => {
  const { children } = props;
  return (
    <Navbar bg="dark">
      <Nav className="flex-grow-1">{children}</Nav>
    </Navbar>
  );
};
