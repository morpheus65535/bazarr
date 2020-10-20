import React from "react";
import { Navbar, Nav, Button, ButtonProps } from "react-bootstrap";
import { FontAwesomeIcon, FontAwesomeIconProps } from "@fortawesome/react-fontawesome";

interface BtnProps {
  text: string;
  iconProps: FontAwesomeIconProps
  btnProps?: ButtonProps
}

export function CommonHeaderBtn(props: BtnProps): JSX.Element {
  const { text, iconProps, btnProps } = props;
  return (
    <Button variant="dark" className="d-flex flex-column" {...btnProps}>
      <FontAwesomeIcon
        size="lg"
        className="mx-auto"
        {...iconProps}
      ></FontAwesomeIcon>
      <span className="align-bottom text-themecolor small text-center">
        {text}
      </span>
    </Button>
  );
}

export function CommonHeader(props: React.PropsWithChildren<{}>): JSX.Element {
  const { children } = props;
  return (
    <Navbar bg="dark">
      <Nav>{children}</Nav>
    </Navbar>
  );
}
