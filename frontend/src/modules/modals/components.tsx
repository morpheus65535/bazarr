import { FunctionComponent, ReactNode } from "react";
import { Modal } from "react-bootstrap";
import { useModalData } from "./hooks";

interface StandardModalProps {
  title: string;
  footer?: ReactNode;
}

export const StandardModalView: FunctionComponent<StandardModalProps> = ({
  children,
  footer,
  title,
}) => {
  const { closeable } = useModalData();
  return (
    <>
      <Modal.Header closeButton={closeable}>{title}</Modal.Header>
      <Modal.Body>{children}</Modal.Body>
      <Modal.Footer hidden={footer === undefined}>{footer}</Modal.Footer>
    </>
  );
};
