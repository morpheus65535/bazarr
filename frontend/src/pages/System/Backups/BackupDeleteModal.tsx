import { AsyncButton } from "@/components";
import {
  useModal,
  useModalControl,
  usePayload,
  withModal,
} from "@/modules/modals";
import { Button } from "@mantine/core";
import React, { FunctionComponent } from "react";
import { useDeleteBackups } from "../../../apis/hooks";

const SystemBackupDeleteModal: FunctionComponent = () => {
  const { mutateAsync } = useDeleteBackups();

  const result = usePayload<string>();

  const Modal = useModal();
  const { hide } = useModalControl();

  const footer = (
    <div className="d-flex flex-row-reverse flex-grow-1 justify-content-between">
      <div>
        <Button
          color="outline-secondary"
          className="mr-2"
          onClick={() => hide()}
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
          onSuccess={() => hide()}
        >
          Delete
        </AsyncButton>
      </div>
    </div>
  );

  return (
    <Modal title="Delete Backup" footer={footer}>
      <span>Are you sure you want to delete the backup '{result}'?</span>
    </Modal>
  );
};

export default withModal(SystemBackupDeleteModal, "delete");
