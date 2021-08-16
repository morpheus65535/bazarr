import React, { FunctionComponent, useCallback, useState } from "react";
import { Modal } from "react-bootstrap";
import { useIsModalShow } from ".";
import { useCloseModal } from "./hooks";

export interface BaseModalProps {
  modalKey: string;
  size?: "sm" | "lg" | "xl";
  closeable?: boolean;
  title?: string;
  footer?: JSX.Element;
}

export const BaseModal: FunctionComponent<BaseModalProps> = (props) => {
  const { size, modalKey, title, children, footer } = props;
  const [needExit, setExit] = useState(false);

  const show = useIsModalShow(modalKey);
  const close = useCloseModal();

  const closeable = props.closeable !== false;

  const hide = useCallback(() => {
    setExit(true);
  }, []);

  const exit = useCallback(() => {
    close();
    setExit(false);
  }, [close]);

  return (
    <Modal
      centered
      size={size}
      show={show && !needExit}
      onHide={hide}
      onExited={exit}
      backdrop={closeable ? undefined : "static"}
    >
      <Modal.Header closeButton={closeable}>{title}</Modal.Header>
      <Modal.Body>{children}</Modal.Body>
      <Modal.Footer hidden={footer === undefined}>{footer}</Modal.Footer>
    </Modal>
  );
};

export default BaseModal;
