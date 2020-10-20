import React from "react";
import {} from "react-bootstrap";

interface InfoProps {
  title: string;
}
type Props = React.PropsWithChildren<InfoProps>;

function TitleBlock(props: Props): JSX.Element {
  const { title, children } = props;
  return (
    <div className="my-4">
      <h4>{title}</h4>
      <hr></hr>
      {children}
    </div>
  );
}

export default TitleBlock;
