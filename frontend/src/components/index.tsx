import React, { FunctionComponent, MouseEvent } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconProp } from "@fortawesome/fontawesome-svg-core";
import { Badge } from "react-bootstrap";

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

interface SettingGroupProps {
  name: string;
}

export const SettingGroup: FunctionComponent<SettingGroupProps> = (props) => {
  const { name, children } = props;
  return (
    <div className="my-4">
      <h4>{name}</h4>
      <hr></hr>
      {children}
    </div>
  );
};

export * from "./CommonForm";
export { default as ItemOverview } from "./ItemOverview";
export { default as LanguageSelector } from "./LanguageSelector";
export { default as EditItemModal } from "./EditItemModal";
export * from "./ContentHeader";
export * from "./tables";
