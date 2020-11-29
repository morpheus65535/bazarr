import React, { FunctionComponent } from "react";
import { Navbar, Nav, Button, ButtonProps } from "react-bootstrap";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";

interface CHButtonProps {
  iconProps: FontAwesomeIconProps;
  btnProps?: ButtonProps;
}

type GroupPosition = "start" | "end";
interface GroupProps {
  pos: GroupPosition;
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

const ContentHeaderGroup: FunctionComponent<GroupProps> = (props) => {
  const { children, pos: dir } = props;

  const className = `d-flex flex-grow-1 justify-content-${dir}`;
  return <div className={className}>{children}</div>;
};

const ContentHeader: FunctionComponent = (props) => {
  const { children } = props;
  return (
    <Navbar bg="dark">
      <Nav className="flex-grow-1">{children}</Nav>
    </Navbar>
  );
};

declare type Header = typeof ContentHeader & {
  Button: typeof ContentHeaderButton;
  Group: typeof ContentHeaderGroup;
};
declare const Header: Header;
export default Header;
