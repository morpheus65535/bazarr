import {
  hideModalAction,
  showModalAction,
} from "@/modules/redux/actions/modal";
import { useReduxAction, useReduxStore } from "@/modules/redux/hooks/base";
import { useCallback, useMemo } from "react";

export function useModalControl() {
  const showModal = useReduxAction(showModalAction);

  const show = useCallback(
    (key: string, payload?: unknown) => {
      showModal({ key, payload });
    },
    [showModal]
  );

  const hide = useReduxAction(hideModalAction);

  return { show, hide };
}

export function useIsShowed(key: string) {
  const stack = useReduxStore((s) => s.modal.stack);

  return useMemo(() => stack.findIndex((m) => m.key === key), [stack, key]);
}

export function usePayload<T>(key: string): T | null {
  const stack = useReduxStore((s) => s.modal.stack);

  return useMemo(
    () => (stack.find((m) => m.key === key)?.payload as T) ?? null,
    [stack, key]
  );
}
