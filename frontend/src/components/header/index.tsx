import clsx from "clsx";
import React, { FunctionComponent } from "react";
import { Row } from "react-bootstrap";
import ContentHeaderButton, { ContentHeaderAsyncButton } from "./Button";
import ContentHeaderGroup from "./Group";

interface Props {
  scroll?: boolean;
  className?: string;
}

declare type Header = FunctionComponent<Props> & {
  Button: typeof ContentHeaderButton;
  AsyncButton: typeof ContentHeaderAsyncButton;
  Group: typeof ContentHeaderGroup;
};

export const ContentHeader: Header = ({ children, scroll, className }) => {
  let childItem: React.ReactNode;

  if (scroll !== false) {
    childItem = (
      <div className="d-flex flex-nowrap flex-grow-1">{children}</div>
    );
  } else {
    childItem = children;
  }
  return (
    <Row
      className={clsx("content-header", "bg-dark p-2", className, {
        scroll: scroll !== false,
      })}
    >
      {childItem}
    </Row>
  );
};

ContentHeader.Button = ContentHeaderButton;
ContentHeader.Group = ContentHeaderGroup;
ContentHeader.AsyncButton = ContentHeaderAsyncButton;

export default ContentHeader;
