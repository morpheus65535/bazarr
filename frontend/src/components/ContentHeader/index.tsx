import React, { FunctionComponent } from "react";
import { Navbar, Nav, Row } from "react-bootstrap";

import ContentHeaderButton from "./Button";
import ContentHeaderGroup from "./Group";

export const ContentHeader: FunctionComponent = (props) => {
  const { children } = props;
  return (
    <Row className="content-header">
      <Navbar bg="dark" className="flex-grow-1">
        <Nav className="flex-grow-1">{children}</Nav>
      </Navbar>
    </Row>
  );
};

export default ContentHeader;
export { ContentHeaderButton, ContentHeaderGroup };

// declare type Header = typeof ContentHeader & {
//   Button: typeof ContentHeaderButton;
//   Group: typeof ContentHeaderGroup;
// };
// declare const Header: Header;
// export default Header;
