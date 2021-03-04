import { faSync } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { systemUpdateTasks } from "../../@redux/actions";
import { useReduxAction, useReduxStore } from "../../@redux/hooks/base";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import { useAutoUpdate } from "../../utilites";
import Table from "./table";

interface Props {}

const SystemTasksView: FunctionComponent<Props> = () => {
  const tasks = useReduxStore((s) => s.system.tasks);
  const update = useReduxAction(systemUpdateTasks);

  // TODO: Use Websocket
  useAutoUpdate(update, 10 * 1000);

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

export default SystemTasksView;
