import React from "react";
import { Col, Form, Row } from "react-bootstrap";

import "./CommonForm.css";

interface FormProps {
  title: string;
}

export function CommonFormGroup(
  props: React.PropsWithChildren<FormProps>
): JSX.Element {
  const { title, children } = props;
  return (
    <Row>
      <Col sm={3} className="mb-3">
        <b>{title}</b>
      </Col>
      <Form.Group
        as={Col}
        sm={7}
        className="d-flex flex-column common-form-group"
      >
        {children}
      </Form.Group>
    </Row>
  );
}
