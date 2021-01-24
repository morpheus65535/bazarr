import React, { FunctionComponent, useState, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { UpdateSystemLogs } from "../../@redux/actions";

import { faTrash, faDownload, faSync } from "@fortawesome/free-solid-svg-icons";
import { ContentHeader, ContentHeaderButton } from "../../components";

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
        <title>Providers - Bazarr (System)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeaderButton
          updating={loading}
          icon={faSync}
          disabled={loading}
          onClick={update}
        >
          Refresh
        </ContentHeaderButton>
        <ContentHeaderButton icon={faDownload}>Download</ContentHeaderButton>
        <ContentHeaderButton
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
        </ContentHeaderButton>
      </ContentHeader>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(mapStateToProps, { update: UpdateSystemLogs })(
  SystemLogsView
);
