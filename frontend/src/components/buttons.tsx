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
  icon: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}> = ({ icon, onClick }) => {
  return (
    <Button
      as={Badge}
      className="mx-1 p-1"
      variant="secondary"
      onClick={onClick}
    >
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    </Button>
  );
};

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

interface AsyncButtonProps<T> {
  as?: ButtonProps["as"];
  variant?: ButtonProps["variant"];
  size?: ButtonProps["size"];

  className?: string;
  disabled?: boolean;
  onChange?: (v: boolean) => void;

  promise: () => Promise<T>;
  onSuccess?: (result: T) => void;
  error?: () => void;
}

export function AsyncButton<T>(
  props: PropsWithChildren<AsyncButtonProps<T>>
): JSX.Element {
  const {
    children,
    className,
    promise,
    onSuccess: success,
    error,
    onChange,
    disabled,
    ...button
  } = props;

  const [loading, setLoading] = useState(false);

  return (
    <Button
      className={className}
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
