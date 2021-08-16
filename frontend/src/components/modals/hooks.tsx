import { useCallback, useContext, useMemo } from "react";
import { useDidUpdate } from "rooks";
import { log } from "../../utilites/logger";
import { ModalContext } from "./provider";

interface ModalInformation<T> {
  isShow: boolean;
  payload: T | null;
  closeModal: ReturnType<typeof useCloseModal>;
}

export function useModalInformation<T>(key: string): ModalInformation<T> {
  const isShow = useIsModalShow(key);
  const payload = useModalPayload<T>(key);
  const closeModal = useCloseModal();

  return useMemo(
    () => ({
      isShow,
      payload,
      closeModal,
    }),
    [isShow, payload, closeModal]
  );
}

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
    control: { pop, peek },
  } = useContext(ModalContext);
  return useCallback(
    (key?: string) => {
      const modal = peek();
      if (key) {
        if (modal?.key === key) {
          pop();
        }
      } else {
        pop();
      }
    },
    [pop, peek]
  );
}

export function useCloseModalIfCovered() {
  const {
    control: { pop, peek },
  } = useContext(ModalContext);
  return useCallback(
    (key: string) => {
      let modal = peek();
      if (modal && modal.key !== key) {
        pop();
      }
    },
    [pop, peek]
  );
}

export function useModalIsCovered(key: string) {
  const { modals } = useContext(ModalContext);
  return useMemo(() => {
    const idx = modals.findIndex((v) => v.key === key);
    return idx !== -1 && idx !== 0;
  }, [modals, key]);
}

export function useIsModalShow(key: string) {
  const {
    control: { peek },
  } = useContext(ModalContext);
  const modal = peek();
  return key === modal?.key;
}

export function useOnModalShow<T>(
  callback: (payload: T | null) => void,
  key: string
) {
  const {
    modals,
    control: { peek },
  } = useContext(ModalContext);
  useDidUpdate(() => {
    const modal = peek();
    if (modal && modal.key === key) {
      callback(modal.payload ?? null);
    }
  }, [modals.length, key]);
}

export function useModalPayload<T>(key: string): T | null {
  const {
    control: { peek },
  } = useContext(ModalContext);
  return useMemo(() => {
    const modal = peek();
    if (modal && modal.key === key) {
      return (modal.payload as T) ?? null;
    } else {
      return null;
    }
  }, [key, peek]);
}
