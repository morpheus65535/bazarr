import React, { FunctionComponent } from "react";
import { Col, Form, Row } from "react-bootstrap";

interface GroupProps {
  header: string;
  hidden?: boolean;
}

export const Group: FunctionComponent<GroupProps> = ({
  header,
  hidden,
  children,
}) => {
  return (
    <Row hidden={hidden} className="flex-column mt-3">
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
