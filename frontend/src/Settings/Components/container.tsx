import React, { FunctionComponent, useState } from "react";
import { Col, Form, Row, Collapse } from "react-bootstrap";

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
  hidden?: boolean;
}

export const Input: FunctionComponent<InputProps> = ({
  children,
  name,
  hidden,
}) => {
  return (
    <Form.Group hidden={hidden}>
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

interface SelectionBoxProps {
  control: (change: React.Dispatch<string | undefined>) => JSX.Element;
  defaultKey?: string;
  indent?: boolean;
  children: (key: string | undefined) => JSX.Element;
}

export const SelectionBox: FunctionComponent<SelectionBoxProps> = ({
  control,
  children,
  indent,
  defaultKey,
}) => {
  const cls: string[] = [];

  const [open, setOpen] = useState(defaultKey);

  if (indent) {
    cls.push("pl-4");
  }

  return (
    <React.Fragment>
      {control(setOpen)}
      <div className={cls.join(" ")}>{children(open)}</div>
    </React.Fragment>
  );
};
