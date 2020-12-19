import React, { FunctionComponent } from "react";
import { Modal } from "react-bootstrap";

export interface ModalProps {
  size?: "sm" | "lg" | "xl";
  closeable?: boolean;
  show: boolean;
  title?: string;
  onClose: () => void;
  footer?: JSX.Element;
}

const BasicModal: FunctionComponent<ModalProps> = (props) => {
  const { size, closeable, show, title, onClose, children, footer } = props;

  const canClose = closeable !== undefined ? closeable : true;

  return (
    <Modal
      centered
      size={size}
      show={show}
      onHide={onClose}
      backdrop={canClose ? undefined : "static"}
    >
      <Modal.Header closeButton={canClose}>{title}</Modal.Header>
      <Modal.Body>{children}</Modal.Body>
      <Modal.Footer hidden={footer === undefined}>{footer}</Modal.Footer>
    </Modal>
  );
};

export default BasicModal;
