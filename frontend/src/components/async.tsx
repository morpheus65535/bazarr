import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  PropsWithChildren,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Alert, Button, Container } from "react-bootstrap";
import { LoadingIndicator } from ".";
import { Selector, SelectorProps } from "./inputs";

interface AsyncStateOverlayProps<T> {
  state: AsyncState<T>;
  exist?: (item: T) => boolean;
  children: (item: NonNullable<T>, error?: Error) => JSX.Element;
}

function defaultExist(item: any) {
  if (item instanceof Array) {
    return item.length !== 0;
  } else {
    return item !== null && item !== undefined;
  }
}

export function AsyncStateOverlay<T>(
  props: PropsWithChildren<AsyncStateOverlayProps<T>>
) {
  const { exist, state, children } = props;
  const missing = exist ? !exist(state.items) : !defaultExist(state.items);

  const reload = useCallback(() => {
    window.location.reload();
  }, []);

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
              <Button variant="outline-danger" onClick={reload}>
                Reload
              </Button>
            </div>
          </Alert>
        </Container>
      );
    }
  }

  return children(state.items!, state.error);
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
      state.items.map((v) => ({
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
