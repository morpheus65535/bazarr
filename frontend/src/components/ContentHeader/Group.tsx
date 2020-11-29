import React, { FunctionComponent } from "react";
import { } from "react-bootstrap";

type GroupPosition = "start" | "end";
interface GroupProps {
  pos: GroupPosition;
}

const ContentHeaderGroup: FunctionComponent<GroupProps> = (props) => {
  const { children, pos: dir } = props;

  const className = `d-flex flex-grow-1 justify-content-${dir}`;
  return <div className={className}>{children}</div>;
};

export default ContentHeaderGroup;