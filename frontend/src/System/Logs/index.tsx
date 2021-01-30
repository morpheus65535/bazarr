import React, { FunctionComponent, useState, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { systemUpdateLogs } from "../../@redux/actions";

import { faTrash, faDownload, faSync } from "@fortawesome/free-solid-svg-icons";
import { ContentHeader } from "../../components";

import Table from "./table";

import { SystemApi } from "../../apis";

interface Props {
  loading: boolean;
  update: () => void;
}

function mapStateToProps({ system }: StoreState) {
  const { logs } = system;
  return {
    loading: logs.updating,
  };
}

const SystemLogsView: FunctionComponent<Props> = ({ loading, update }) => {
  useEffect(() => update(), [update]);

  const [resetting, setReset] = useState(false);

  return (
    <Container fluid>
      <Helmet>
        <title>Logs - Bazarr (System)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Button
          updating={loading}
          icon={faSync}
          disabled={loading}
          onClick={update}
        >
          Refresh
        </ContentHeader.Button>
        <ContentHeader.Button icon={faDownload}>Download</ContentHeader.Button>
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
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(mapStateToProps, { update: systemUpdateLogs })(
  SystemLogsView
);
