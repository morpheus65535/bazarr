import React, { FunctionComponent } from "react";
import {} from "react-bootstrap";

interface Props {
  name: string;
}

const SettingGroup: FunctionComponent<Props> = (props) => {
  const { name, children } = props;
  return (
    <div className="my-4">
      <h4>{name}</h4>
      <hr></hr>
      {children}
    </div>
  );
};

export default SettingGroup;
