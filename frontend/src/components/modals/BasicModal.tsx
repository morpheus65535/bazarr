import React, { FunctionComponent } from "react";
import { Modal } from "react-bootstrap";

export interface ModalProps {
  item?: ExtendItem;
  onClose: () => void;
  footer?: JSX.Element;
}

const BasicModal: FunctionComponent<ModalProps> = (props) => {
  const { item, onClose, children, footer } = props;
  return (
    <Modal size="lg" show={item !== undefined} onHide={onClose}>
      <Modal.Header closeButton>{item?.title}</Modal.Header>
      <Modal.Body>{children}</Modal.Body>
      <Modal.Footer hidden={footer === undefined}>{footer}</Modal.Footer>
    </Modal>
  );
};

export default BasicModal;
