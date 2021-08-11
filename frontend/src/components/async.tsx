import {
  faCheck,
  faCircleNotch,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { isEmpty } from "lodash";
import React, {
  FunctionComponent,
  PropsWithChildren,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Button, ButtonProps } from "react-bootstrap";
import { LoadingIndicator } from ".";
import { Selector, SelectorProps } from "./inputs";

interface Props<T extends Async.Base<any>> {
  ctx: T;
  children: FunctionComponent<T>;
}

export function AsyncOverlay<T extends Async.Base<any>>(props: Props<T>) {
  const { ctx, children } = props;
  if (
    ctx.state === "uninitialized" ||
    (ctx.state === "loading" && isEmpty(ctx.content))
  ) {
    return <LoadingIndicator></LoadingIndicator>;
  } else if (ctx.state === "failed") {
    return <p>{ctx.error}</p>;
  } else {
    return children(ctx);
  }
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

type AsyncSelectorProps<V, T extends Async.Base<V[]>> = {
  state: T;
  update: () => void;
  label: (item: V) => string;
};

type RemovedSelectorProps<T, M extends boolean> = Omit<
  SelectorProps<T, M>,
  "loading" | "options" | "onFocus"
>;

export function AsyncSelector<
  V,
  T extends Async.Base<V[]>,
  M extends boolean = false
>(props: Override<AsyncSelectorProps<V, T>, RemovedSelectorProps<V, M>>) {
  const { label, state, update, ...selector } = props;

  const options = useMemo<SelectorOption<V>[]>(
    () =>
      state.content.map((v) => ({
        label: label(v),
        value: v,
      })),
    [state, label]
  );

  return (
    <Selector
      loading={state.state === "loading"}
      options={options}
      label={label}
      onFocus={() => {
        if (state.state === "uninitialized") {
          update();
        }
      }}
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
