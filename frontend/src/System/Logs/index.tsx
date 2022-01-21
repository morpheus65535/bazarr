import { faDownload, faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useCallback } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useDeleteLogs, useSystemLogs } from "../../apis/queries/client";
import { ContentHeader, QueryOverlay } from "../../components";
import { Environment } from "../../utilities";
import Table from "./table";

interface Props {}

const SystemLogsView: FunctionComponent<Props> = () => {
  const logs = useSystemLogs();

  const { mutate, isLoading } = useDeleteLogs();

  const download = useCallback(() => {
    window.open(`${Environment.baseUrl}/bazarr.log`);
  }, []);

  return (
    <QueryOverlay {...logs}>
      {({ data, isFetching, refetch }) => (
        <Container fluid>
          <Helmet>
            <title>Logs - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={isFetching}
              icon={faSync}
              onClick={() => refetch()}
            >
              Refresh
            </ContentHeader.Button>
            <ContentHeader.Button icon={faDownload} onClick={download}>
              Download
            </ContentHeader.Button>
            <ContentHeader.Button
              updating={isLoading}
              icon={faTrash}
              onClick={() => mutate()}
            >
              Empty
            </ContentHeader.Button>
          </ContentHeader>
          <Row>
            <Table logs={data ?? []}></Table>
          </Row>
        </Container>
      )}
    </QueryOverlay>
  );
};

export default SystemLogsView;
