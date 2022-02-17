import {
  BaseModal,
  BaseModalProps,
  useCloseModal,
  useModalPayload,
} from "components";
import React, { FunctionComponent } from "react";
import { Button } from "react-bootstrap";

interface Props extends BaseModalProps {}

const SystemBackupDeleteModal: FunctionComponent<Props> = ({ ...modal }) => {
  const result = useModalPayload<string>(modal.modalKey);

  const closeModal = useCloseModal();

  const footer = (
    <div className="d-flex flex-row-reverse flex-grow-1 justify-content-between">
      <div>
        <Button
          variant="outline-secondary"
          className="mr-2"
          onClick={() => {
            closeModal();
          }}
        >
          Cancel
        </Button>
        <Button
          onClick={() => {
            closeModal();
          }}
        >
          Delete
        </Button>
      </div>
    </div>
  );

  return (
    <BaseModal title="Delete Backup" footer={footer} {...modal}>
      Are you sure you want to delete the backup '{result}'?
    </BaseModal>
  );
};

export default SystemBackupDeleteModal;
