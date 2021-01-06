import React, { FunctionComponent } from "react";
import { Col, Form, Row } from "react-bootstrap";

interface GroupProps {
  header: string;
}

export const Group: FunctionComponent<GroupProps> = ({ header, children }) => {
  return (
    <Row className="flex-column">
      <Col>
        <h4>{header}</h4>
        <hr></hr>
      </Col>
      <Col>{children}</Col>
    </Row>
  );
};

export interface ContainerProps {
  name?: string;
}

export const Input: FunctionComponent<ContainerProps> = ({
  children,
  name,
}) => {
  return (
    <Form.Group>
      {name && <Form.Label>{name}</Form.Label>}
      {children}
    </Form.Group>
  );
};

export const Message: FunctionComponent<{
  type: "warning" | "info";
}> = ({ type, children }) => {
  return (
    <Form.Text className={type === "warning" ? "text-warning" : "text-muted"}>
      {children}
    </Form.Text>
  );
};
