import React, { FunctionComponent } from "react";

type GroupPosition = "start" | "end";
interface GroupProps {
  pos: GroupPosition;
}

const ContentHeaderGroup: FunctionComponent<GroupProps> = (props) => {
  const { children, pos } = props;

  const className = `d-flex flex-grow-1 align-items-center justify-content-${pos}`;
  return <div className={className}>{children}</div>;
};

export default ContentHeaderGroup;
