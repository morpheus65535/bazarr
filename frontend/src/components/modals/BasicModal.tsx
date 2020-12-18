import React, { FunctionComponent } from "react";
import { Modal } from "react-bootstrap";

export interface ModalProps {
  size?: "sm" | "lg" | "xl";
  show: boolean;
  title?: string;
  onClose: () => void;
  footer?: JSX.Element;
}

const BasicModal: FunctionComponent<ModalProps> = (props) => {
  const { size, show, title, onClose, children, footer } = props;
  return (
    <Modal centered size={size} show={show} onHide={onClose}>
      <Modal.Header closeButton>{title}</Modal.Header>
      <Modal.Body>{children}</Modal.Body>
      <Modal.Footer hidden={footer === undefined}>{footer}</Modal.Footer>
    </Modal>
  );
};

export default BasicModal;
