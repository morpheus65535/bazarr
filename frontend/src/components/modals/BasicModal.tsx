import React, { FunctionComponent } from "react";
import { Modal } from "react-bootstrap";
import { useIsModalShow } from ".";
import { useCloseModal } from "./provider";

export interface BasicModalProps {
  modalKey: string;
  size?: "sm" | "lg" | "xl";
  closeable?: boolean;
  title?: string;
  footer?: JSX.Element;
}

export const BasicModal: FunctionComponent<BasicModalProps> = (props) => {
  const { size, closeable, modalKey, title, children, footer } = props;

  const show = useIsModalShow(modalKey);
  const closeModal = useCloseModal();

  const canClose = closeable !== undefined ? closeable : true;

  return (
    <Modal
      centered
      size={size}
      show={show}
      onHide={closeModal}
      backdrop={canClose ? undefined : "static"}
    >
      <Modal.Header closeButton={canClose}>{title}</Modal.Header>
      <Modal.Body>{children}</Modal.Body>
      <Modal.Footer hidden={footer === undefined}>{footer}</Modal.Footer>
    </Modal>
  );
};

export default BasicModal;
