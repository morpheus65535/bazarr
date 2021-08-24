import { useCallback, useContext, useMemo } from "react";
import { useDidUpdate } from "rooks";
import { log } from "../../utilities/logger";
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
    control: { pop },
  } = useContext(ModalContext);
  return useCallback(
    (key?: string) => {
      pop(key);
    },
    [pop]
  );
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
