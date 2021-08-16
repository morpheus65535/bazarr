import { useCallback, useContext, useMemo } from "react";
import { useDidUpdate } from "rooks";
import { log } from "../../utilites/logger";
import { ModalContext } from "./provider";

export function useShowModal() {
  const {
    control: { push },
  } = useContext(ModalContext);

  return useCallback(
    <T,>(key: string, payload?: T) => {
      log("info", `modal ${key} sending payload`, payload);

      push({ key, payload });
    },
    [push]
  );
}

export function useCloseModal() {
  const {
    control: { pop },
  } = useContext(ModalContext);
  return pop;
}

export function useCloseModalUntil() {
  const {
    control: { pop, peek },
  } = useContext(ModalContext);
  return useCallback(
    (key: string) => {
      let modal = peek();
      while (modal) {
        if (modal.key === key) {
          break;
        } else {
          modal = pop();
        }
      }
    },
    [pop, peek]
  );
}

export function useIsModalShow(key: string) {
  const {
    control: { peek },
  } = useContext(ModalContext);
  const modal = peek();
  return key === modal?.key;
}

export function useOnModalShow(callback: () => void, key: string) {
  const isShow = useIsModalShow(key);
  useDidUpdate(() => {
    if (isShow) {
      callback();
    }
  }, [isShow]);
}

export function usePayload<T>(key: string): T | null {
  const {
    control: { peek },
  } = useContext(ModalContext);
  return useMemo(() => {
    const modal = peek();
    if (modal && modal.key === key) {
      return modal.payload as T;
    } else {
      return null;
    }
  }, [key, peek]);
}
