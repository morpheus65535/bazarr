/* eslint-disable @typescript-eslint/ban-types */
import { useModals as useMantineModals } from "@mantine/modals";
import { ModalSettings } from "@mantine/modals/lib/context";
import { useCallback, useContext, useMemo } from "react";
import { ModalComponent, ModalIdContext } from "./WithModal";

export function useModals() {
  const {
    openContextModal: openMantineContextModal,
    closeContextModal: closeContextModalRaw,
    ...rest
  } = useMantineModals();

  const openContextModal = useCallback(
    <ARGS extends {}>(
      modal: ModalComponent<ARGS>,
      props: ARGS,
      settings?: ModalSettings
    ) => {
      openMantineContextModal(modal.modalKey, {
        ...modal.settings,
        ...settings,
        innerProps: props,
      });
    },
    [openMantineContextModal]
  );

  const closeContextModal = useCallback(
    (modal: ModalComponent) => {
      rest.closeModal(modal.modalKey);
    },
    [rest]
  );

  const id = useContext(ModalIdContext);

  const closeSelf = useCallback(() => {
    if (id) {
      rest.closeModal(id);
    }
  }, [id, rest]);

  // TODO: Performance
  return useMemo(
    () => ({ openContextModal, closeContextModal, closeSelf, ...rest }),
    [closeContextModal, closeSelf, openContextModal, rest]
  );
}
