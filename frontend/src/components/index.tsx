import React, { FunctionComponent, MouseEvent } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { Badge, Spinner, Button, Row, Col, Form } from "react-bootstrap";
import {
  faCheckCircle,
  faTimesCircle,
  faTrash,
  faDownload,
  faUser,
  faRecycle,
  faCloudUploadAlt,
  faClock,
} from "@fortawesome/free-solid-svg-icons";

import "./style.css";

export const ActionBadge: FunctionComponent<{
  onClick?: (e: MouseEvent) => void;
}> = (props) => {
  const { children, onClick } = props;
  return (
    <Button
      as={Badge}
      className="mx-1 p-1"
      variant="secondary"
      onClick={(event) => {
        event.preventDefault();
        onClick && onClick(event);
      }}
    >
      {children}
    </Button>
  );
};

interface ActionIconDefinitions {
  icon: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}

export const ActionIcon: FunctionComponent<ActionIconDefinitions> = (props) => {
  const { icon, onClick } = props;
  return (
    <ActionBadge onClick={onClick}>
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    </ActionBadge>
  );
};

enum HistoryAction {
  Delete = 0,
  Download,
  Manual,
  Upgrade,
  Upload,
  Sync,
}

export const HistoryIcon: FunctionComponent<{ action: number }> = (props) => {
  const { action } = props;
  let icon = null;
  switch (action) {
    case HistoryAction.Delete:
      icon = faTrash;
      break;
    case HistoryAction.Download:
      icon = faDownload;
      break;
    case HistoryAction.Manual:
      icon = faUser;
      break;
    case HistoryAction.Sync:
      icon = faClock;
      break;
    case HistoryAction.Upgrade:
      icon = faRecycle;
      break;
    case HistoryAction.Upload:
      icon = faCloudUploadAlt;
      break;
  }
  if (icon) {
    return <FontAwesomeIcon icon={icon}></FontAwesomeIcon>;
  } else {
    return null;
  }
};

export const CommonFormGroup: FunctionComponent<{ title: string }> = (
  props
) => {
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
};

export const SettingGroup: FunctionComponent<{ name: string }> = (props) => {
  const { name, children } = props;
  return (
    <div className="my-4 flex-grow-1">
      <h4>{name}</h4>
      <hr></hr>
      {children}
    </div>
  );
};

export const LoadingIndicator: FunctionComponent = (props) => {
  return (
    <div className="d-flex flex-grow-1 justify-content-center my-5">
      <Spinner animation="border"></Spinner>
    </div>
  );
};

export const BooleanIndicator: FunctionComponent<{ value: boolean }> = (
  props
) => {
  return (
    <FontAwesomeIcon
      icon={props.value ? faCheckCircle : faTimesCircle}
    ></FontAwesomeIcon>
  );
};

export { default as ItemOverview } from "./ItemOverview";
export { default as LanguageSelector } from "./LanguageSelector";
export { default as AsyncStateOverlay } from "./AsyncStateOverlay";
export * from "./Modals";
export * from "./ContentHeader";
export * from "./Tables";
