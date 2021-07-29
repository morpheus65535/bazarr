import { faSync } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useSystemTasks } from "../../@redux/hooks";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {}

const SystemTasksView: FunctionComponent<Props> = () => {
  const [tasks, update] = useSystemTasks();

  return (
    <AsyncStateOverlay state={tasks}>
      {({ data }) => (
        <Container fluid>
          <Helmet>
            <title>Tasks - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={tasks.state === "loading"}
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
