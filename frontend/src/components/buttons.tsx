import React, {
  FunctionComponent,
  MouseEvent,
  PropsWithChildren,
  useState,
} from "react";
import { Button, ButtonProps, Badge } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";

import { faCircleNotch } from "@fortawesome/free-solid-svg-icons";

export const ActionBadge: FunctionComponent<{
  onClick?: (e: MouseEvent) => void;
}> = (props) => {
  const { children, onClick } = props;
  return (
    <Button
      as={Badge}
      className="mx-1 p-1"
      variant="secondary"
      onClick={onClick}
    >
      {children}
    </Button>
  );
};

export const ActionIconBadge: FunctionComponent<{
  icon: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}> = ({ icon, onClick }) => {
  return (
    <ActionBadge onClick={onClick}>
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    </ActionBadge>
  );
};

interface AsyncButtonProps<T> {
  variant?: ButtonProps["variant"];
  size?: ButtonProps["size"];
  disabled?: boolean;
  onChange?: (v: boolean) => void;

  promise: () => Promise<T>;
  success?: (result: T) => void;
  error?: () => void;
}

export const ActionIcon: FunctionComponent<{
  icon: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}> = ({ icon, onClick }) => {
  return (
    <Button size="sm" className="mx-1" variant="light" onClick={onClick}>
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    </Button>
  );
};

export function AsyncButton<T>(
  props: PropsWithChildren<AsyncButtonProps<T>>
): JSX.Element {
  const {
    children,
    promise,
    success,
    error,
    onChange,
    disabled,
    ...button
  } = props;

  const [loading, setLoading] = useState(false);

  return (
    <Button
      disabled={loading || disabled}
      {...button}
      onClick={() => {
        setLoading(true);
        onChange && onChange(true);
        promise()
          .then(success)
          .catch(error)
          .finally(() => {
            setLoading(false);
            onChange && onChange(false);
          });
      }}
    >
      {loading ? (
        <FontAwesomeIcon icon={faCircleNotch} spin></FontAwesomeIcon>
      ) : (
        children
      )}
    </Button>
  );
}
