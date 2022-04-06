import { useCreateBackups, useSystemBackups } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { QueryOverlay } from "@/components/async";
import { faFileArchive } from "@fortawesome/free-solid-svg-icons";
import { Container } from "@mantine/core";
import React, { FunctionComponent } from "react";
import { Helmet } from "react-helmet";
import Table from "./table";

const SystemBackupsView: FunctionComponent = () => {
  const backups = useSystemBackups();

  const { mutate: backup, isLoading: isResetting } = useCreateBackups();

  return (
    <QueryOverlay result={backups}>
      <Container fluid px={0}>
        <Helmet>
          <title>Backups - Bazarr (System)</title>
        </Helmet>
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
