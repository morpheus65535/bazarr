import {
  faCheck,
  faCircleNotch,
  faExclamationTriangle,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  PropsWithChildren,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Alert, Button, ButtonProps, Container } from "react-bootstrap";
import { LoadingIndicator } from ".";
import { useNotification } from "../@redux/hooks/site";
import { Reload } from "../utilites";
import { Selector, SelectorProps } from "./inputs";

enum RequestState {
  Success,
  Error,
  Invalid,
}

interface ChildProps<T> {
  data: NonNullable<Readonly<T>>;
  error?: Error;
}

interface AsyncStateOverlayProps<T> {
  state: AsyncState<T>;
  exist?: (item: T) => boolean;
  children?: FunctionComponent<ChildProps<T>>;
}

function defaultExist(item: any) {
  if (item instanceof Array) {
    return item.length !== 0;
  } else {
    return item !== null && item !== undefined;
  }
}

export function AsyncStateOverlay<T>(props: AsyncStateOverlayProps<T>) {
  const { exist, state, children } = props;
  const missing = exist ? !exist(state.data) : !defaultExist(state.data);

  const onError = useNotification("async-overlay");

  useEffect(() => {
    if (!state.updating && state.error !== undefined && !missing) {
      onError({
        type: "error",
        message: state.error.message,
      });
    }
  }, [state, onError, missing]);

  if (state.updating) {
    if (missing) {
      return <LoadingIndicator></LoadingIndicator>;
    }
  } else {
    if (state.error && missing) {
      return (
        <Container>
          <Alert variant="danger" className="my-4">
            <Alert.Heading>
              <FontAwesomeIcon
                className="mr-2"
                icon={faExclamationTriangle}
              ></FontAwesomeIcon>
              <span>Ouch! You got an error</span>
            </Alert.Heading>
            <p>{state.error.message}</p>
            <hr></hr>
            <div className="d-flex justify-content-end">
              <Button variant="outline-danger" onClick={Reload}>
                Reload
              </Button>
            </div>
          </Alert>
        </Container>
      );
    }
  }

  return children ? children({ data: state.data!, error: state.error }) : null;
}

interface PromiseProps<T> {
  promise: () => Promise<T>;
  children: FunctionComponent<T>;
}

export function PromiseOverlay<T>({ promise, children }: PromiseProps<T>) {
  const [item, setItem] = useState<T | null>(null);

  useEffect(() => {
    promise()
      .then((result) => setItem(result))
      .catch(() => {});
  }, [promise]);

  if (item === null) {
    return <LoadingIndicator></LoadingIndicator>;
  } else {
    return children(item);
  }
}

type ExtractAS<T extends AsyncState<any[]>> = Unpacked<AsyncPayload<T>>;

type AsyncSelectorProps<T extends AsyncState<any[]>> = {
  state: T;
  label: (item: ExtractAS<T>) => string;
};

type RemovedSelectorProps<T, M extends boolean> = Omit<
  SelectorProps<T, M>,
  "loading" | "options"
>;

export function AsyncSelector<
  T extends AsyncState<any[]>,
  M extends boolean = false
>(
  props: Override<AsyncSelectorProps<T>, RemovedSelectorProps<ExtractAS<T>, M>>
) {
  const { label, state, ...selector } = props;

  const options = useMemo<SelectorOption<ExtractAS<T>>[]>(
    () =>
      state.data.map((v) => ({
        label: label(v),
        value: v,
      })),
    [state, label]
  );

  return (
    <Selector
      loading={state.updating}
      options={options}
      label={label}
      {...selector}
    ></Selector>
  );
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

  const [, setHandle] = useState<Nullable<NodeJS.Timeout>>(null);

  useEffect(() => {
    if (noReset) {
      return;
    }

    if (state === RequestState.Error || state === RequestState.Success) {
      const handle = setTimeout(() => setState(RequestState.Invalid), 2 * 1000);
      setHandle(handle);
    }

    // Clear timeout handle so we wont leak memory
    return () => {
      setHandle((handle) => {
        if (handle) {
          clearTimeout(handle);
        }
        return null;
      });
    };
  }, [state, noReset]);

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
