import { useCreateBackups, useSystemBackups } from "@/apis/hooks";
import { ContentHeader } from "@/components";
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
        <ContentHeader>
          <ContentHeader.Button
            icon={faFileArchive}
            updating={isResetting}
            onClick={() => backup()}
          >
            Backup Now
          </ContentHeader.Button>
        </ContentHeader>
        <Table backups={backups.data ?? []}></Table>
      </Container>
    </QueryOverlay>
  );
};

export default SystemBackupsView;
