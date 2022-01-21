import { faSync } from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { useSystemTasks } from "../../apis/queries/client";
import { ContentHeader, QueryOverlay } from "../../components";
import Table from "./table";

interface Props {}

const SystemTasksView: FunctionComponent<Props> = () => {
  const tasks = useSystemTasks();

  const { isFetching, data, refetch } = tasks;

  return (
    <QueryOverlay result={tasks}>
      <Container fluid>
        <Helmet>
          <title>Tasks - Bazarr (System)</title>
        </Helmet>
        <ContentHeader>
          <ContentHeader.Button
            updating={isFetching}
            icon={faSync}
            onClick={() => refetch()}
          >
            Refresh
          </ContentHeader.Button>
        </ContentHeader>
        <Row>
          <Table tasks={data ?? []}></Table>
        </Row>
      </Container>
    </QueryOverlay>
  );
};

export default SystemTasksView;
