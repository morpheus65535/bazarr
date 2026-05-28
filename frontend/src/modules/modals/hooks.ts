import { useCallback, useContext, useMemo } from "react";
import { openModal, useModals as useMantineModals } from "@mantine/modals";
import { ModalComponent, ModalIdContext } from "./WithModal";

type ModalSettings = Parameters<typeof openModal>[0];

export function useModals() {
  const { openContextModal: openMantineContextModal, ...rest } =
    useMantineModals();

  const openContextModal = useCallback(
    <ARGS extends {}>(
      modal: ModalComponent<ARGS>,
      props: ARGS,
      settings?: ModalSettings,
    ) => {
      openMantineContextModal(modal.modalKey, {
        ...modal.settings,
        ...settings,
        innerProps: props,
      });
    },
    [openMantineContextModal],
  );

  const closeContext = useCallback(
    (modal: ModalComponent) => {
      rest.closeModal(modal.modalKey);
    },
    [rest],
  );

  const id = useContext(ModalIdContext);

  const closeSelf = useCallback(() => {
    if (id) {
      rest.closeModal(id);
    }
  }, [id, rest]);

  // TODO: Performance
  return useMemo(
    () => ({ openContextModal, closeContext, closeSelf, ...rest }),
    [closeContext, closeSelf, openContextModal, rest],
  );
}
