import React, { FunctionComponent, MouseEvent, useMemo, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import {
  Badge,
  Spinner,
  Button,
  Dropdown,
} from "react-bootstrap";
import {
  faCheck,
  faTimes,
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

export const ActionIcon: FunctionComponent<{
  icon: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}> = (props) => {
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

type SelectorOptions = {
  [key: string]: string;
};

export interface SelectorProps {
  options: SelectorOptions;
  noneKey?: string;
  defaultKey?: string;
  multiply?: boolean;
  disabled?: boolean;
  onChanged?: (key: string) => void;
}

export const Selector: FunctionComponent<SelectorProps> = ({
  options,
  noneKey,
  defaultKey,
  multiply,
  disabled,
  onChanged,
}) => {
  const [selectKey, setSelect] = useState(defaultKey ? defaultKey : noneKey);
  const items = useMemo(() => {
    const its: JSX.Element[] = [];
    for (const key in options) {
      const value = options[key];
      its.push(
        <Dropdown.Item
          key={key}
          onClick={() => {
            setSelect(key);
            onChanged && onChanged(key);
          }}
        >
          {value}
        </Dropdown.Item>
      );
    }
    return its;
  }, [options, onChanged]);

  let text: string;

  if (selectKey) {
    text = options[selectKey];
  } else {
    text = "Select...";
  }

  return (
    <Dropdown defaultValue={selectKey}>
      <Dropdown.Toggle
        disabled={disabled}
        block
        className="text-left"
        variant="outline-secondary"
      >
        {text}
      </Dropdown.Toggle>
      <Dropdown.Menu>{items}</Dropdown.Menu>
    </Dropdown>
  );
};

export const LoadingIndicator: FunctionComponent = () => {
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
    <FontAwesomeIcon icon={props.value ? faCheck : faTimes}></FontAwesomeIcon>
  );
};

export { default as ItemOverview } from "./ItemOverview";
export { default as LanguageSelector } from "./LanguageSelector";
export { default as AsyncStateOverlay } from "./AsyncStateOverlay";
export * from "./Modals";
export * from "./ContentHeader";
export * from "./Tables";
