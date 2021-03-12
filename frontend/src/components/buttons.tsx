import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { faCircleNotch } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  MouseEvent,
  PropsWithChildren,
  useState,
} from "react";
import { Badge, Button, ButtonProps } from "react-bootstrap";

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

interface ActionIconProps extends ActionIconItemProps {
  disabled?: boolean;
  destructive?: boolean;
  variant?: string;
  onClick?: (e: MouseEvent) => void;
  className?: string;
  size?: ButtonProps["size"];
}

export const ActionIcon: FunctionComponent<ActionIconProps> = ({
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
      size={size}
      variant={variant ?? "light"}
      className={`text-nowrap ${className ?? ""}`}
      onClick={onClick}
    >
      <ActionIconItem {...other}></ActionIconItem>
    </Button>
  );
};

interface ActionIconItemProps {
  loading?: boolean;
  icon: IconDefinition;
  children?: string;
}

export const ActionIconItem: FunctionComponent<ActionIconItemProps> = ({
  icon,
  children,
  loading,
}) => {
  return (
    <React.Fragment>
      <FontAwesomeIcon
        style={{ width: "1rem" }}
        icon={loading ? faCircleNotch : icon}
        spin={loading}
      ></FontAwesomeIcon>
      {children && !loading ? (
        <span className="ml-2 font-weight-bold">{children}</span>
      ) : null}
    </React.Fragment>
  );
};

interface AsyncButtonProps<T> {
  as?: ButtonProps["as"];
  variant?: ButtonProps["variant"];
  size?: ButtonProps["size"];

  className?: string;
  disabled?: boolean;
  onChange?: (v: boolean) => void;

  promise: () => Promise<T> | null;
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
        const result = promise();

        if (result) {
          setLoading(true);
          onChange && onChange(true);
          result
            .then(success)
            .catch(error)
            .finally(() => {
              setLoading(false);
              onChange && onChange(false);
            });
        }
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
