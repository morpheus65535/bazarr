import React, { FunctionComponent, MouseEvent } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconProp } from "@fortawesome/fontawesome-svg-core";
import { Badge, Spinner } from "react-bootstrap";
import { faCheckCircle, faTimesCircle } from "@fortawesome/free-solid-svg-icons";

interface ActionIconProps {
  icon: IconProp;
  onClick?: (e: MouseEvent) => void;
}

export const ActionIcon: FunctionComponent<ActionIconProps> = (props) => {
  const { icon, onClick } = props;
  return (
    <Badge
      as="a"
      href=""
      variant="secondary"
      className="mx-1"
      onClick={(event: MouseEvent) => {
        event.preventDefault();
        onClick && onClick(event);
      }}
    >
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    </Badge>
  );
};

export const SettingGroup: FunctionComponent<{name: string}> = (props) => {
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
    <FontAwesomeIcon icon={props.value ? faCheckCircle : faTimesCircle}></FontAwesomeIcon>
  );
};

export * from "./CommonForm";
export { default as ItemOverview } from "./ItemOverview";
export { default as LanguageSelector } from "./LanguageSelector";
export { default as EditItemModal } from "./EditItemModal";
export { default as AsyncStateOverlay } from "./AsyncStateOverlay";
export { default as HistoryActionIcon } from "./HistoryActionIcon";
export * from "./ActionModal";
export * from "./ContentHeader";
export * from "./tables";
