import React, { FunctionComponent, MouseEvent } from "react";
import { Button } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { faSpinner } from "@fortawesome/free-solid-svg-icons";

interface CHButtonProps {
  disabled?: boolean;
  icon: IconDefinition;
  updating?: boolean;
  updatingIcon?: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}

const ContentHeaderButton: FunctionComponent<CHButtonProps> = (props) => {
  const { children, icon, disabled, updating, updatingIcon, onClick } = props;

  let displayIcon = icon;
  if (updating) {
    displayIcon = updatingIcon ? updatingIcon : faSpinner;
  }

  return (
    <Button
      variant="dark"
      className="d-flex flex-column text-nowrap py-1"
      disabled={disabled || updating}
      onClick={onClick}
    >
      <FontAwesomeIcon
        className="mx-auto my-1"
        icon={displayIcon}
        spin={updating}
      ></FontAwesomeIcon>
      <span className="align-bottom text-themecolor small text-center">
        {children}
      </span>
    </Button>
  );
};

export default ContentHeaderButton;
