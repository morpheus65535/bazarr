import { faFileArchive } from "@fortawesome/free-solid-svg-icons";
import { useCreateBackups, useSystemBackups } from "apis/hooks";
import { ContentHeader, QueryOverlay } from "components";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import Table from "./table";

interface Props {}

const SystemBackupsView: FunctionComponent<Props> = () => {
  const backups = useSystemBackups();

  const { mutate: backup, isLoading: isResetting } = useCreateBackups();

  return (
    <QueryOverlay result={backups}>
      <Container fluid>
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
        <Row>
          <Table backups={backups.data ?? []}></Table>
        </Row>
      </Container>
    </QueryOverlay>
  );
};

export default SystemBackupsView;
