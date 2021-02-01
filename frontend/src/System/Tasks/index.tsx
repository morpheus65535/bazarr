import { faSync } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { systemUpdateTasks } from "../../@redux/actions";
import { ContentHeader } from "../../components";
import Table from "./table";

interface Props {
  update: () => void;
  loading: boolean;
}

function mapStateToProps({ system }: StoreState) {
  const { tasks } = system;
  return {
    loading: tasks.updating,
  };
}

const SystemTasksView: FunctionComponent<Props> = ({ update, loading }) => {
  useEffect(() => update(), [update]);

  return (
    <Container fluid>
      <Helmet>
        <title>Tasks - Bazarr (System)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Button updating={loading} icon={faSync} onClick={update}>
          Refresh
        </ContentHeader.Button>
      </ContentHeader>
      <Row>
        <Table></Table>
      </Row>
    </Container>
  );
};

export default connect(mapStateToProps, { update: systemUpdateTasks })(
  SystemTasksView
);
