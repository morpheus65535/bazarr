import React from "react";
import { Col, Form, Row } from "react-bootstrap";

interface FormProps {
  title: string;
}

export function CommonFormGroup(
  props: React.PropsWithChildren<FormProps>
): JSX.Element {
  const { title, children } = props;
  return (
    <Row>
      <Col sm={3}>
        <b>{title}</b>
      </Col>
      <Form.Group as={Col}>{children}</Form.Group>
    </Row>
  );
}
