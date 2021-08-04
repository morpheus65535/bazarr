import { faSync } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useSystemTasks } from "../../@redux/hooks";
import { AsyncOverlay, ContentHeader } from "../../components";
import Table from "./table";

interface Props {}

const SystemTasksView: FunctionComponent<Props> = () => {
  const [tasks, update] = useSystemTasks();

  return (
    <AsyncOverlay ctx={tasks}>
      {({ content, state }) => (
        <Container fluid>
          <Helmet>
            <title>Tasks - Bazarr (System)</title>
          </Helmet>
          <ContentHeader>
            <ContentHeader.Button
              updating={state === "loading"}
              icon={faSync}
              onClick={update}
            >
              Refresh
            </ContentHeader.Button>
          </ContentHeader>
          <Row>
            <Table tasks={content}></Table>
          </Row>
        </Container>
      )}
    </AsyncOverlay>
  );
};

export default SystemTasksView;
