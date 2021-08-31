import React, { FunctionComponent, useMemo } from "react";
import { Row } from "react-bootstrap";
import ContentHeaderButton, { ContentHeaderAsyncButton } from "./Button";
import ContentHeaderGroup from "./Group";
import "./style.scss";

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
  const cls = useMemo(() => {
    const rowCls = ["content-header", "bg-dark", "p-2"];

    if (className !== undefined) {
      rowCls.push(className);
    }

    if (scroll !== false) {
      rowCls.push("scroll");
    }
    return rowCls.join(" ");
  }, [scroll, className]);

  let childItem: React.ReactNode;

  if (scroll !== false) {
    childItem = (
      <div className="d-flex flex-nowrap flex-grow-1">{children}</div>
    );
  } else {
    childItem = children;
  }
  return <Row className={cls}>{childItem}</Row>;
};

ContentHeader.Button = ContentHeaderButton;
ContentHeader.Group = ContentHeaderGroup;
ContentHeader.AsyncButton = ContentHeaderAsyncButton;

export default ContentHeader;
