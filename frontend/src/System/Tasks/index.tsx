import { faSync } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { systemUpdateTasks } from "../../@redux/actions";
import { useReduxAction, useReduxStore } from "../../@redux/hooks/base";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {}

const SystemTasksView: FunctionComponent<Props> = () => {
  const tasks = useReduxStore((s) => s.system.tasks);
  const update = useReduxAction(systemUpdateTasks);

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

export default SystemTasksView;
