import MutateButton from "@/components/async/MutateButton";
import {
  useModal,
  useModalControl,
  usePayload,
  withModal,
} from "@/modules/modals";
import { Button, Text } from "@mantine/core";
import React, { FunctionComponent } from "react";
import { useDeleteBackups } from "../../../apis/hooks";

const SystemBackupDeleteModal: FunctionComponent = () => {
  const remove = useDeleteBackups();

  const result = usePayload<string>();

  const Modal = useModal();
  const { hide } = useModalControl();

  const footer = (
    <div className="d-flex flex-row-reverse flex-grow-1 justify-content-between">
      <div>
        <Button
          color="gray"
          variant="outline"
          className="mr-2"
          onClick={() => hide()}
        >
          Cancel
        </Button>
        <MutateButton
          noReset
          mutation={remove}
          args={() => result ?? null}
          onSuccess={() => hide()}
        >
          Delete
        </MutateButton>
      </div>
    </div>
  );

  return (
    <Modal title="Delete Backup" footer={footer}>
      <Text>Are you sure you want to delete the backup '{result}'?</Text>
    </Modal>
  );
};

export default withModal(SystemBackupDeleteModal, "delete");
