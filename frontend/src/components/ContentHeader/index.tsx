import React, { FunctionComponent } from "react";
import { Row } from "react-bootstrap";

import ContentHeaderButton from "./Button";
import ContentHeaderGroup from "./Group";

export const ContentHeader: FunctionComponent = (props) => {
  const { children } = props;
  return (
    <Row className="content-header">
      <div className="d-flex flex-nowrap flex-grow-1 bg-dark p-2">
        {children}
      </div>
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
