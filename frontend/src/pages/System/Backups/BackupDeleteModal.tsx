import { AsyncButton, BaseModal, BaseModalProps } from "@/components";
import { useModalControl, usePayload } from "@/modules/redux/hooks/modal";
import React, { FunctionComponent } from "react";
import { Button } from "react-bootstrap";
import { useDeleteBackups } from "../../../apis/hooks";

interface Props extends BaseModalProps {}

const SystemBackupDeleteModal: FunctionComponent<Props> = ({ ...modal }) => {
  const { mutateAsync } = useDeleteBackups();

  const result = usePayload<string>(modal.modalKey);

  const { hide } = useModalControl();

  const footer = (
    <div className="d-flex flex-row-reverse flex-grow-1 justify-content-between">
      <div>
        <Button
          variant="outline-secondary"
          className="mr-2"
          onClick={() => {
            hide(modal.modalKey);
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
          onSuccess={() => hide(modal.modalKey)}
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
