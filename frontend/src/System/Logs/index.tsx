import { faDownload, faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useCallback, useState } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useSystemLogs } from "../../@redux/hooks";
import { SystemApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import { useBaseUrl } from "../../utilites";
import Table from "./table";

interface Props {}

const SystemLogsView: FunctionComponent<Props> = () => {
  const [logs, update] = useSystemLogs();

  const [resetting, setReset] = useState(false);

  const baseUrl = useBaseUrl(true);

  const download = useCallback(() => {
    window.open(`${baseUrl}bazarr.log`);
  }, [baseUrl]);

  return (
    <AsyncStateOverlay state={logs}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Logs - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={logs.updating}
              icon={faSync}
              onClick={update}
            >
              Refresh
            </ContentHeader.Button>
            <ContentHeader.Button icon={faDownload} onClick={download}>
              Download
            </ContentHeader.Button>
            <ContentHeader.Button
              updating={resetting}
              icon={faTrash}
              onClick={() => {
                setReset(true);
                SystemApi.deleteLogs().finally(() => {
                  setReset(false);
                  update();
                });
              }}
            >
              Empty
            </ContentHeader.Button>
          </ContentHeader>
          <Row>
            <Table logs={data}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default SystemLogsView;
