import { useIsShowed, useModalControl } from "@/modules/redux/hooks/modal";
import clsx from "clsx";
import { FunctionComponent, useCallback, useState } from "react";
import { Modal } from "react-bootstrap";

export interface BaseModalProps {
  modalKey: string;
  size?: "sm" | "lg" | "xl";
  closeable?: boolean;
  title?: string;
  footer?: JSX.Element;
}

export const BaseModal: FunctionComponent<BaseModalProps> = (props) => {
  const { size, modalKey, title, children, footer, closeable = false } = props;
  const [needExit, setExit] = useState(false);

  const { hide: hideModal } = useModalControl();
  const showIndex = useIsShowed(modalKey);
  const isShowed = showIndex !== -1;

  const hide = useCallback(() => {
    setExit(true);
  }, []);

  const exit = useCallback(() => {
    if (isShowed) {
      hideModal(modalKey);
    }
    setExit(false);
  }, [isShowed, hideModal, modalKey]);

  return (
    <Modal
      centered
      size={size}
      show={isShowed && !needExit}
      onHide={hide}
      onExited={exit}
      backdrop={closeable ? undefined : "static"}
      className={clsx(`index-${showIndex}`)}
      backdropClassName={clsx(`index-${showIndex}`)}
    >
      <Modal.Header closeButton={closeable}>{title}</Modal.Header>
      <Modal.Body>{children}</Modal.Body>
      <Modal.Footer hidden={footer === undefined}>{footer}</Modal.Footer>
    </Modal>
  );
};

export default BaseModal;
