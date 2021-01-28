import React, {
  Dispatch,
  FunctionComponent,
  useEffect,
  useState,
  useContext,
  useCallback,
} from "react";

const ModalContext = React.createContext<[string, Dispatch<string>]>([
  "",
  (s) => {},
]);

const PayloadContext = React.createContext<[any, Dispatch<any>]>([
  undefined,
  (p) => {},
]);

export function useShowModal() {
  const modal = useContext(ModalContext)[1];
  const update = useContext(PayloadContext)[1];
  return useCallback(
    <T,>(key: string, payload?: T) => {
      if (process.env.NODE_ENV === "development") {
        console.log(`modal ${key} sending payload`, payload);
      }
      update(payload);
      modal(key);
    },
    [modal, update]
  );
}

export function useCloseModal() {
  const modal = useContext(ModalContext)[1];
  const payload = useContext(PayloadContext)[1];
  return useCallback(() => {
    modal("");
    payload(undefined);
  }, [modal, payload]);
}

export function useIsModalShow(key: string) {
  const currentKey = useContext(ModalContext)[0];
  return key === currentKey;
}

export function usePayload<T>(key: string): T | undefined {
  const payload = useContext(PayloadContext)[0];
  const show = useIsModalShow(key);
  return show ? (payload as T) : undefined;
}

export function useWhenModalShow(key: string, callback: React.EffectCallback) {
  const show = useIsModalShow(key);

  useEffect(() => {
    if (show) {
      return callback();
    }
  }, [show]); // eslint-disable-line react-hooks/exhaustive-deps
}

export function useWhenPayloadUpdate(
  key: string,
  callback: React.EffectCallback
) {
  const [last, setLast] = useState<any>(undefined);
  const payload = usePayload(key);

  useWhenModalShow(key, () => {
    if (payload !== last) {
      setLast(payload);
      callback();
    }
  });
}

interface Props {
  value?: [string, any];
}

export const ModalProvider: FunctionComponent<Props> = ({
  children,
  value,
}) => {
  const [key, setKey] = useState("");
  const [payload, setPayload] = useState<any>(undefined);

  useEffect(() => {
    if (value) {
      setKey(value[0]);
      setPayload(value[1]);
    } else {
      setKey("");
      setPayload(undefined);
    }
  }, [value]);

  return (
    <ModalContext.Provider value={[key, setKey]}>
      <PayloadContext.Provider value={[payload, setPayload]}>
        {children}
      </PayloadContext.Provider>
    </ModalContext.Provider>
  );
};
