import React, { FunctionComponent } from "react";
import { Modal, Tabs, Tab, Container } from "react-bootstrap";

export interface TabElement {
  title: string;
  event: string;
  element: JSX.Element;
}

interface ModalProps {
  title: string;
  show: boolean;
  active?: string;
  close: () => void;
  tabs: TabElement[];
}

export const ActionModal: FunctionComponent<ModalProps> = ({
  title,
  show,
  active,
  close,
  tabs,
}) => {
  const tabElements = React.useMemo(
    () =>
      tabs.map((val) => (
        <Tab eventKey={val.event} key={val.event} title={val.title}>
          <Container fluid className="p-2">
            {val.element}
          </Container>
        </Tab>
      )),
    [tabs]
  );
  return (
    <Modal size="lg" show={show} onHide={close}>
      <Modal.Header closeButton>{title}</Modal.Header>
      <Modal.Body>
        <Tabs defaultActiveKey={active}>{tabElements}</Tabs>
      </Modal.Body>
    </Modal>
  );
};
