import React, {
  FunctionComponent,
  Dispatch,
  useEffect,
  useState,
  useCallback,
  useContext,
  useMemo,
} from "react";

const ModalContext = React.createContext<[string[], Dispatch<string[]>]>([
  [],
  (s) => {},
]);

const PayloadContext = React.createContext<[any[], Dispatch<any[]>]>([
  [],
  (p) => {},
]);

export function useShowModal() {
  const [keys, setKeys] = useContext(ModalContext);
  const [payloads, setPayloads] = useContext(PayloadContext);
  return useCallback(
    <T,>(key: string, payload?: T) => {
      if (process.env.NODE_ENV === "development") {
        console.log(`modal ${key} sending payload`, payload);
      }

      setKeys([...keys, key]);
      setPayloads([...payloads, payload]);
    },
    [keys, payloads, setKeys, setPayloads]
  );
}

export function useCloseModal() {
  const [keys, setKeys] = useContext(ModalContext);
  const [payloads, setPayloads] = useContext(PayloadContext);
  return useCallback(() => {
    const newKey = [...keys];
    newKey.pop();
    const newPayload = [...payloads];
    newPayload.pop();
    setKeys(newKey);
    setPayloads(newPayload);
  }, [keys, payloads, setKeys, setPayloads]);
}

export function useIsModalShow(key: string) {
  const keys = useContext(ModalContext)[0];
  return key === keys[keys.length - 1];
}

export function usePayload<T>(key: string): T | undefined {
  const payloads = useContext(PayloadContext)[0];
  const keys = useContext(ModalContext)[0];
  return useMemo(() => {
    const idx = keys.findIndex((v) => v === key);
    const show = idx !== -1 && idx === keys.length - 1;
    return show ? (payloads[idx] as T) : undefined;
  }, [keys, payloads]);
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

export const ModalProvider: FunctionComponent = ({ children }) => {
  const [key, setKey] = useState<string[]>([]);
  const [payload, setPayload] = useState<any[]>([]);

  return (
    <ModalContext.Provider value={[key, setKey]}>
      <PayloadContext.Provider value={[payload, setPayload]}>
        {children}
      </PayloadContext.Provider>
    </ModalContext.Provider>
  );
};
