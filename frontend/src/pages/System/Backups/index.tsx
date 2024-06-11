import { FunctionComponent } from "react";
import { Container } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { faFileArchive } from "@fortawesome/free-solid-svg-icons";
import { useCreateBackups, useSystemBackups } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import Table from "./table";

const SystemBackupsView: FunctionComponent = () => {
  const backups = useSystemBackups();

  const { mutate: backup, isPending: isResetting } = useCreateBackups();

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
