import React, { FunctionComponent } from "react";
import { Row } from "react-bootstrap";
import ContentHeaderButton, { ContentHeaderAsyncButton } from "./Button";
import ContentHeaderGroup from "./Group";
import "./style.scss";

interface Props {
  scroll?: boolean;
}

declare type Header = FunctionComponent<Props> & {
  Button: typeof ContentHeaderButton;
  AsyncButton: typeof ContentHeaderAsyncButton;
  Group: typeof ContentHeaderGroup;
};

export const ContentHeader: Header = ({ children, scroll }) => {
  const rowCls = ["content-header", "bg-dark", "p-2"];

  let childItem: React.ReactNode;

  if (scroll !== false) {
    rowCls.push("scroll");
    childItem = (
      <div className="d-flex flex-nowrap flex-grow-1">{children}</div>
    );
  } else {
    childItem = children;
  }
  return <Row className={rowCls.join(" ")}>{childItem}</Row>;
};

ContentHeader.Button = ContentHeaderButton;
ContentHeader.Group = ContentHeaderGroup;
ContentHeader.AsyncButton = ContentHeaderAsyncButton;

export default ContentHeader;
