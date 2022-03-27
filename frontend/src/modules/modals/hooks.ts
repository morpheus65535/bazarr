import {
  hideModalAction,
  showModalAction,
} from "@/modules/redux/actions/modal";
import { useReduxAction, useReduxStore } from "@/modules/redux/hooks/base";
import { useCallback, useContext, useEffect, useMemo, useRef } from "react";
import { StandardModalView } from "./components";
import {
  ModalData,
  ModalDataContext,
  ModalSetterContext,
} from "./ModalContext";
import { ModalComponent } from "./WithModal";

type ModalProps = Partial<Omit<ModalData, "key">> & {
  onMounted?: () => void;
};

export function useModal(props?: ModalProps): typeof StandardModalView {
  const setter = useContext(ModalSetterContext);

  useEffect(() => {
    if (setter && props) {
      setter.closeable(props.closeable ?? true);
      setter.size(props.size);
    }
  }, [props, setter]);

  const ref = useRef<ModalProps["onMounted"]>(props?.onMounted);
  ref.current = props?.onMounted;

  const layer = useCurrentLayer();

  useEffect(() => {
    if (layer !== -1 && ref.current) {
      ref.current();
    }
  }, [layer]);

  return StandardModalView;
}

export function useModalControl() {
  const showAction = useReduxAction(showModalAction);

  const show = useCallback(
    <P>(comp: ModalComponent<P>, payload?: unknown) => {
      showAction({ key: comp.modalKey, payload });
    },
    [showAction]
  );

  const hideAction = useReduxAction(hideModalAction);

  const hide = useCallback(
    (key?: string) => {
      hideAction(key);
    },
    [hideAction]
  );

  return { show, hide };
}

export function useModalData(): ModalData {
  const data = useContext(ModalDataContext);

  if (data === null) {
    throw new Error("useModalData should be used inside Modal");
  }

  return data;
}

export function usePayload<T>(): T | null {
  const { key } = useModalData();
  const stack = useReduxStore((s) => s.modal.stack);

  return useMemo(
    () => (stack.find((m) => m.key === key)?.payload as T) ?? null,
    [stack, key]
  );
}

export function useCurrentLayer() {
  const { key } = useModalData();
  const stack = useReduxStore((s) => s.modal.stack);

  return useMemo(() => stack.findIndex((m) => m.key === key), [stack, key]);
}
