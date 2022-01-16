import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { faCircleNotch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, MouseEvent } from "react";
import { Badge, Button, ButtonProps } from "react-bootstrap";

export const ActionBadge: FunctionComponent<{
  icon: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}> = ({ icon, onClick }) => {
  return (
    <Badge
      as={Button}
      className="mx-1 p-1"
      variant="secondary"
      bg="secondary"
      onClick={onClick}
    >
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    </Badge>
  );
};

interface ActionButtonProps extends ActionButtonItemProps {
  disabled?: boolean;
  destructive?: boolean;
  variant?: string;
  onClick?: (e: MouseEvent) => void;
  className?: string;
  size?: ButtonProps["size"];
}

export const ActionButton: FunctionComponent<ActionButtonProps> = ({
  onClick,
  destructive,
  disabled,
  variant,
  className,
  size,
  ...other
}) => {
  return (
    <Button
      disabled={other.loading || disabled}
      size={size ?? "sm"}
      variant={variant ?? "light"}
      className={`text-nowrap ${className ?? ""}`}
      onClick={onClick}
    >
      <ActionButtonItem {...other}></ActionButtonItem>
    </Button>
  );
};

interface ActionButtonItemProps {
  loading?: boolean;
  alwaysShowText?: boolean;
  icon: IconDefinition;
  children?: string;
}

export const ActionButtonItem: FunctionComponent<ActionButtonItemProps> = ({
  icon,
  children,
  loading,
  alwaysShowText,
}) => {
  const showText = alwaysShowText === true || loading !== true;
  return (
    <React.Fragment>
      <FontAwesomeIcon
        style={{ width: "1rem" }}
        icon={loading ? faCircleNotch : icon}
        spin={loading}
      ></FontAwesomeIcon>
      {children && showText ? (
        <span className="ms-2 font-weight-bold">{children}</span>
      ) : null}
    </React.Fragment>
  );
};
