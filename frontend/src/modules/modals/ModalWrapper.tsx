import { Modal } from "@mantine/core";
import clsx from "clsx";
import { FunctionComponent, useCallback, useState } from "react";
import { useCurrentLayer, useModalControl, useModalData } from "./hooks";

interface Props {}

export const ModalWrapper: FunctionComponent<Props> = ({ children }) => {
  const { size, closeable, key } = useModalData();
  const [needExit, setExit] = useState(false);

  const { hide: hideModal } = useModalControl();

  const layer = useCurrentLayer();
  const isShowed = layer !== -1;

  const hide = useCallback(() => {
    setExit(true);
  }, []);

  const exit = useCallback(() => {
    if (isShowed) {
      hideModal(key);
    }
    setExit(false);
  }, [isShowed, hideModal, key]);

  return (
    <Modal
      centered
      size={size}
      show={isShowed && !needExit}
      onHide={hide}
      onExited={exit}
      backdrop={closeable ? undefined : "static"}
      className={clsx(`index-${layer}`)}
      backdropClassName={clsx(`index-${layer}`)}
    >
      {children}
    </Modal>
  );
};

export default ModalWrapper;
