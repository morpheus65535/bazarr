import {
  BaseModal,
  BaseModalProps,
  useCloseModal,
  useModalPayload,
} from "components";
import React, { FunctionComponent } from "react";
import { Button } from "react-bootstrap";

interface Props extends BaseModalProps {}

const SystemBackupRestoreModal: FunctionComponent<Props> = ({ ...modal }) => {
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
          Restore
        </Button>
      </div>
    </div>
  );

  return (
    <BaseModal title="Restore Backup" footer={footer} {...modal}>
      Are you sure you want to restore the backup '{result}'? Bazarr will
      automatically restart and reload the UI during the restore process.
    </BaseModal>
  );
};

export default SystemBackupRestoreModal;
