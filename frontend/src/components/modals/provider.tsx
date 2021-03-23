import React, {
  Dispatch,
  FunctionComponent,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { log } from "../../utilites/logger";

const ModalContext = React.createContext<[string[], Dispatch<string[]>]>([
  [],
  (s) => {},
]);

const PayloadContext = React.createContext<[any[], Dispatch<any[]>]>([
  [],
  (p) => {},
]);

// TODO: Performance
export function useShowModal() {
  const [keys, setKeys] = useContext(ModalContext);
  const [payloads, setPayloads] = useContext(PayloadContext);
  return useCallback(
    <T,>(key: string, payload?: T) => {
      log("info", `modal ${key} sending payload`, payload);

      setKeys([...keys, key]);
      setPayloads([...payloads, payload ?? null]);
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

export function useCloseModalUntil(key: string) {
  const [keys, setKeys] = useContext(ModalContext);
  const [payloads, setPayloads] = useContext(PayloadContext);
  return useCallback(() => {
    const idx = keys.findIndex((v) => v === key);
    if (idx !== -1) {
      const newKey = keys.slice(0, idx + 1);
      const newPayload = payloads.slice(0, idx + 1);
      setKeys(newKey);
      setPayloads(newPayload);
    } else {
      log("error", "Cannot close modal, key is unavailable");
    }
  }, [keys, payloads, setKeys, setPayloads, key]);
}

export function useIsModalShow(key: string) {
  const keys = useContext(ModalContext)[0];
  return key === keys[keys.length - 1];
}

export function useOnModalShow(key: string, show: () => void) {
  const isShow = useIsModalShow(key);
  useEffect(() => {
    if (isShow) {
      show();
    }
  }, [isShow, show]);
}

export function usePayload<T>(key: string): T | null {
  const payloads = useContext(PayloadContext)[0];
  const keys = useContext(ModalContext)[0];
  return useMemo(() => {
    const idx = keys.findIndex((v) => v === key);
    return idx !== -1 ? payloads[idx] : null;
  }, [keys, payloads, key]);
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
