import {
  faCheck,
  faCircleNotch,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  PropsWithChildren,
  useCallback,
  useEffect,
  useState,
} from "react";
import { Button, ButtonProps } from "react-bootstrap";
import { UseQueryResult } from "react-query";
import { useTimeoutWhen } from "rooks";
import { LoadingIndicator } from ".";

interface QueryOverlayProps {
  result: UseQueryResult<unknown, unknown>;
  children: React.ReactElement;
}

export const QueryOverlay: FunctionComponent<QueryOverlayProps> = ({
  children,
  result: { isLoading, isError, error },
}) => {
  if (isLoading) {
    return <LoadingIndicator></LoadingIndicator>;
  } else if (isError) {
    return <p>{error as string}</p>;
  }

  return children;
};

interface PromiseProps<T> {
  promise: () => Promise<T>;
  children: FunctionComponent<T>;
}

export function PromiseOverlay<T>({ promise, children }: PromiseProps<T>) {
  const [item, setItem] = useState<T | null>(null);

  useEffect(() => {
    promise()
      .then(setItem)
      .catch(() => {});
  }, [promise]);

  if (item === null) {
    return <LoadingIndicator></LoadingIndicator>;
  } else {
    return children(item);
  }
}

interface AsyncButtonProps<T> {
  as?: ButtonProps["as"];
  variant?: ButtonProps["variant"];
  size?: ButtonProps["size"];

  className?: string;
  disabled?: boolean;
  onChange?: (v: boolean) => void;

  noReset?: boolean;
  animation?: boolean;

  promise: () => Promise<T> | null;
  onSuccess?: (result: T) => void;
  error?: () => void;
}

enum RequestState {
  Success,
  Error,
  Invalid,
}

export function AsyncButton<T>(
  props: PropsWithChildren<AsyncButtonProps<T>>
): JSX.Element {
  const {
    children: propChildren,
    className,
    promise,
    onSuccess,
    noReset,
    animation,
    error,
    onChange,
    disabled,
    ...button
  } = props;

  const [loading, setLoading] = useState(false);

  const [state, setState] = useState(RequestState.Invalid);

  const needFire = state !== RequestState.Invalid && !noReset;

  useTimeoutWhen(
    () => {
      setState(RequestState.Invalid);
    },
    2 * 1000,
    needFire
  );

  const click = useCallback(() => {
    if (state !== RequestState.Invalid) {
      return;
    }

    const result = promise();

    if (result) {
      setLoading(true);
      onChange && onChange(true);
      result
        .then((res) => {
          setState(RequestState.Success);
          onSuccess && onSuccess(res);
        })
        .catch(() => {
          setState(RequestState.Error);
          error && error();
        })
        .finally(() => {
          setLoading(false);
          onChange && onChange(false);
        });
    }
  }, [error, onChange, promise, onSuccess, state]);

  const showAnimation = animation ?? true;

  let children = propChildren;
  if (showAnimation) {
    if (loading) {
      children = <FontAwesomeIcon icon={faCircleNotch} spin></FontAwesomeIcon>;
    }

    if (state === RequestState.Success) {
      children = <FontAwesomeIcon icon={faCheck}></FontAwesomeIcon>;
    } else if (state === RequestState.Error) {
      children = <FontAwesomeIcon icon={faTimes}></FontAwesomeIcon>;
    }
  }

  return (
    <Button
      className={className}
      disabled={loading || disabled || state !== RequestState.Invalid}
      {...button}
      onClick={click}
    >
      {children}
    </Button>
  );
}
