import { Modal } from "@mantine/core";
import { FunctionComponent, useCallback } from "react";
import { useCurrentLayer, useModalControl, useModalData } from "./hooks";

interface Props {}

export const ModalWrapper: FunctionComponent<Props> = ({ children }) => {
  const { size, closeable, key } = useModalData();

  const { hide: hideModal } = useModalControl();

  const layer = useCurrentLayer();
  const isShowed = layer !== -1;

  const exit = useCallback(() => {
    if (isShowed) {
      hideModal(key);
    }
  }, [isShowed, hideModal, key]);

  return (
    <Modal centered size={size} opened={isShowed} onClose={exit}>
      {children}
    </Modal>
  );
};

export default ModalWrapper;
