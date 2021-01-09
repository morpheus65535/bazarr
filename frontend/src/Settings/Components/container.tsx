import React, { FunctionComponent, useState } from "react";
import { Col, Form, Row, Collapse } from "react-bootstrap";
import { Check, CheckProps } from "./items";

interface GroupProps {
  header: string;
}

export const Group: FunctionComponent<GroupProps> = ({ header, children }) => {
  return (
    <Row className="flex-column mt-3">
      <Col>
        <h4>{header}</h4>
        <hr></hr>
      </Col>
      <Col>{children}</Col>
    </Row>
  );
};

export interface InputProps {
  name?: string;
}

export const Input: FunctionComponent<InputProps> = ({ children, name }) => {
  return (
    <Form.Group>
      {name && <Form.Label>{name}</Form.Label>}
      {children}
    </Form.Group>
  );
};

interface CollapseBoxProps {
  control: (change: React.Dispatch<boolean>) => JSX.Element;
  defaultOpen?: boolean;
  indent?: boolean;
}

export const CollapseBox: FunctionComponent<CollapseBoxProps> = ({
  control,
  children,
  indent,
  defaultOpen,
}) => {
  const cls: string[] = [];

  const [open, setOpen] = useState(defaultOpen ?? false);

  if (indent) {
    cls.push("pl-4");
  }

  return (
    <React.Fragment>
      {control(setOpen)}
      <Collapse in={open}>
        <div className={cls.join(" ")}>{children}</div>
      </Collapse>
    </React.Fragment>
  );
};
