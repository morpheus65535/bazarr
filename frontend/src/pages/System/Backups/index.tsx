import { faFileArchive } from "@fortawesome/free-solid-svg-icons";
import { useSystemBackups } from "apis/hooks";
import { ContentHeader, QueryOverlay } from "components";
import React, { FunctionComponent, useCallback } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Environment } from "../../../utilities";
import Table from "./table";

interface Props {}

const SystemBackupsView: FunctionComponent<Props> = () => {
  const backups = useSystemBackups();

  const run_backup = useCallback(() => {
    window.open(`${Environment.baseUrl}/bazarr.log`);
  }, []);

  return (
    <QueryOverlay result={backups}>
      <Container fluid>
        <Helmet>
          <title>Backups - Bazarr (System)</title>
        </Helmet>
        <ContentHeader>
          <ContentHeader.Button icon={faFileArchive} onClick={run_backup}>
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
