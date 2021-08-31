import { faDownload, faSync, faTrash } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useCallback, useState } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { systemUpdateLogs } from "../../@redux/actions";
import { useSystemLogs } from "../../@redux/hooks";
import { useReduxAction } from "../../@redux/hooks/base";
import { SystemApi } from "../../apis";
import { AsyncOverlay, ContentHeader } from "../../components";
import { Environment } from "../../utilities";
import Table from "./table";

interface Props {}

const SystemLogsView: FunctionComponent<Props> = () => {
  const logs = useSystemLogs();
  const update = useReduxAction(systemUpdateLogs);

  const [resetting, setReset] = useState(false);

  const download = useCallback(() => {
    window.open(`${Environment.baseUrl}/bazarr.log`);
  }, []);

  return (
    <AsyncOverlay ctx={logs}>
      {({ content, state }) => (
        <Container fluid>
          <Helmet>
            <title>Logs - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={state === "loading"}
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
            <Table logs={content ?? []}></Table>
          </Row>
        </Container>
      )}
    </AsyncOverlay>
  );
};

export default SystemLogsView;
