import { FunctionComponent, useCallback, useRef } from "react";
import { Container, Group } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { showNotification } from "@mantine/notifications";
import {
  faCloudUploadAlt,
  faFileArchive,
} from "@fortawesome/free-solid-svg-icons";
import {
  useCreateBackups,
  useSystemBackups,
  useUploadBackups,
} from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { Toolbox, UploadDropzone } from "@/components";
import { QueryOverlay } from "@/components/async";
import { notification } from "@/modules/task";
import Table from "./table";

const SystemBackupsView: FunctionComponent = () => {
  const backups = useSystemBackups();

  const { mutate: backup, isPending: isResetting } = useCreateBackups();

  const { mutate: upload, isPending: isUploading } = useUploadBackups();

  const openDropzone = useRef<VoidFunction>(null);

  const onDrop = useCallback(
    (files: File[]) => {
      if (files.length !== 1) {
        showNotification(
          notification.warn(
            "Cannot Upload Backup",
            "Select a single backup archive at a time",
          ),
        );
        return;
      }
      upload(files[0]);
    },
    [upload],
  );

  useDocumentTitle(`Backups - ${useInstanceName()} (System)`);

  return (
    <QueryOverlay result={backups}>
      <Container fluid px={0}>
        <UploadDropzone
          openRef={openDropzone}
          active={!isUploading}
          onDrop={onDrop}
        ></UploadDropzone>
        <Toolbox>
          <Group gap="xs">
            <Toolbox.Button
              icon={faFileArchive}
              loading={isResetting}
              onClick={() => backup()}
            >
              Backup Now
            </Toolbox.Button>
            <Toolbox.Button
              icon={faCloudUploadAlt}
              loading={isUploading}
              onClick={() => openDropzone.current?.()}
            >
              Upload
            </Toolbox.Button>
          </Group>
        </Toolbox>
        <Table backups={backups.data ?? []}></Table>
      </Container>
    </QueryOverlay>
  );
};

export default SystemBackupsView;
