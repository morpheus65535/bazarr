import { faSync } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { systemUpdateTasks } from "../../@redux/actions";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {
  update: () => void;
  tasks: AsyncState<SystemTaskResult[]>;
}

function mapStateToProps({ system }: StoreState) {
  const { tasks } = system;
  return {
    tasks,
  };
}

const SystemTasksView: FunctionComponent<Props> = ({ update, tasks }) => {
  useEffect(() => {
    // TODO: Use Websocket
    update();
    const handle = setInterval(() => update(), 10 * 1000);
    return () => clearInterval(handle);
  }, [update]);

  return (
    <AsyncStateOverlay state={tasks}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>Tasks - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={tasks.updating}
              icon={faSync}
              onClick={update}
            >
              Refresh
            </ContentHeader.Button>
          </ContentHeader>
          <Row>
            <Table tasks={data}></Table>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: systemUpdateTasks })(
  SystemTasksView
);
