import {
  AsyncButton,
  BaseModal,
  BaseModalProps,
  useCloseModal,
  useModalPayload,
} from "components";
import React, { FunctionComponent } from "react";
import { Button } from "react-bootstrap";
import { useDeleteBackups } from "../../../apis/hooks";

interface Props extends BaseModalProps {}

const SystemBackupDeleteModal: FunctionComponent<Props> = ({ ...modal }) => {
  const result = useModalPayload<string>(modal.modalKey);

  const { mutateAsync } = useDeleteBackups();

  const closeModal = useCloseModal();

  const footer = (
    <div className="d-flex flex-row-reverse flex-grow-1 justify-content-between">
      <div>
        <Button
          variant="outline-secondary"
          className="mr-2"
          onClick={() => {
            closeModal(modal.modalKey);
          }}
        >
          Cancel
        </Button>
        <AsyncButton
          noReset
          promise={() => {
            if (result) {
              return mutateAsync(result);
            } else {
              return null;
            }
          }}
          onSuccess={() => closeModal(modal.modalKey)}
        >
          Delete
        </AsyncButton>
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
