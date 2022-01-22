import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { Card as BSCard, Col, Form, Row } from "react-bootstrap";
import "./style.scss";

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

interface CardProps {
  header?: string;
  subheader?: string;
  plus?: boolean;
  onClick?: () => void;
}

export const ColCard: FunctionComponent<CardProps> = (props) => {
  return (
    <Col className="p-2" xs={6} lg={4}>
      <Card {...props}></Card>
    </Col>
  );
};

export const Card: FunctionComponent<CardProps> = ({
  header,
  subheader,
  plus,
  onClick,
}) => {
  return (
    <BSCard className="settings-card" onClick={() => onClick && onClick()}>
      {plus ? (
        <BSCard.Body className="d-flex justify-content-center align-items-center">
          <FontAwesomeIcon size="2x" icon={faPlus}></FontAwesomeIcon>
        </BSCard.Body>
      ) : (
        <BSCard.Body>
          <BSCard.Title className="text-nowrap text-truncate">
            {header}
          </BSCard.Title>
          <BSCard.Subtitle
            hidden={subheader === undefined}
            className="small text-nowrap text-truncate"
          >
            {subheader}
          </BSCard.Subtitle>
        </BSCard.Body>
      )}
    </BSCard>
  );
};
