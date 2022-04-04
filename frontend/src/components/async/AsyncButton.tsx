import {
  faCheck,
  faCircleNotch,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "@mantine/core";
import { PropsWithChildren, useCallback, useState } from "react";
import { useTimeoutWhen } from "rooks";

interface AsyncButtonProps<T> {
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

export default function AsyncButton<T>(
  props: PropsWithChildren<AsyncButtonProps<T>>
): JSX.Element {
  const {
    children: propChildren,
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
      disabled={loading || disabled || state !== RequestState.Invalid}
      {...button}
      onClick={click}
    >
      {children}
    </Button>
  );
}
