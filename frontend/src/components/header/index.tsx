import { Group } from "@mantine/core";
import { FunctionComponent, ReactNode } from "react";
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
  let childItem: ReactNode;

  if (scroll !== false) {
    childItem = (
      <div className="d-flex flex-nowrap flex-grow-1">{children}</div>
    );
  } else {
    childItem = children;
  }
  return <Group>{childItem}</Group>;
};

ContentHeader.Button = ContentHeaderButton;
ContentHeader.Group = ContentHeaderGroup;
ContentHeader.AsyncButton = ContentHeaderAsyncButton;

export default ContentHeader;
