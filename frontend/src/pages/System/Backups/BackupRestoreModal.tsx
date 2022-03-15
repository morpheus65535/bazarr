import { useRestoreBackups } from "@/apis/hooks/system";
import { AsyncButton, BaseModal, BaseModalProps } from "@/components";
import { useModalControl, usePayload } from "@/modules/redux/hooks/modal";
import React, { FunctionComponent } from "react";
import { Button } from "react-bootstrap";

interface Props extends BaseModalProps {}

const SystemBackupRestoreModal: FunctionComponent<Props> = ({ ...modal }) => {
  const result = usePayload<string>(modal.modalKey);

  const { mutateAsync } = useRestoreBackups();

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
          Restore
        </AsyncButton>
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
