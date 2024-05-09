import { FunctionComponent } from "react";
import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useCreateBackups, useSystemBackups } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import Table from "./table";

import { faFileArchive } from "@fortawesome/free-solid-svg-icons";

const SystemBackupsView: FunctionComponent = () => {
  const backups = useSystemBackups();

  const { mutate: backup, isLoading: isResetting } = useCreateBackups();

  useDocumentTitle("Backups - Bazarr (System)");

  return (
    <QueryOverlay result={backups}>
      <Container fluid px={0}>
        <Toolbox>
          <Toolbox.Button
            icon={faFileArchive}
            loading={isResetting}
            onClick={() => backup()}
          >
            Backup Now
          </Toolbox.Button>
        </Toolbox>
        <Table backups={backups.data ?? []}></Table>
      </Container>
    </QueryOverlay>
  );
};

export default SystemBackupsView;
